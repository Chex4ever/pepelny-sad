"""Overworld input routing."""
from __future__ import annotations

import pygame

from src.audio.tile_sounds import resolve_footstep
from src.constants import CELL_H, CELL_W, MAP_ORIGIN_Y
from src.world.companions import companion_pos_for_player
from src.world.save import load_game, save_game
from src.world.tile_entities import resolve_companion, resolve_player, resolve_world_cell
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, visibility_state


class OverworldInputRouter:
    DRAG_THRESHOLD_PX = 4

    def __init__(self, scene):
        self.scene = scene
        self._panning = False
        self._pan_accum_x = 0.0
        self._pan_accum_y = 0.0
        self._click_pending = False

    def update_mouse_tooltip(self, inp) -> None:
        ow = self.scene
        wx0, wy0 = ow.camera.view_origin()
        world = inp.mouse_world(ow.camera, MAP_ORIGIN_Y)
        if world is None:
            ow.status.set_tooltip("")
            return
        wx, wy = world
        state = visibility_state(wx, wy, ow.visible, ow._is_explored)
        if state == UNEXPLORED:
            ow.status.set_tooltip("Неизвестная земля")
            return
        if (wx, wy) == (ow.player.x, ow.player.y):
            name, _ = resolve_player()
            ow.status.set_tooltip(name, can_examine=True)
            return
        for cid in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ow.player.x, ow.player.y)
            if (wx, wy) == (cx, cy):
                name, _ = resolve_companion(cid)
                ow.status.set_tooltip(name, can_examine=True)
                return
        info = resolve_world_cell(wx, wy, ow.game.world_state.layer, ow.game)
        if info and state == VISIBLE:
            name, _ = info
            ow.status.set_tooltip(name, can_examine=True)
        elif state == EXPLORED:
            ow.status.set_tooltip("Память о месте", can_examine=False)
        else:
            ow.status.set_tooltip("")

    def _handle_map_mouse(self, inp) -> None:
        ow = self.scene
        if inp.mouse_left_down():
            if inp.mouse_on_map(MAP_ORIGIN_Y):
                self._panning = False
                self._pan_accum_x = 0.0
                self._pan_accum_y = 0.0
                self._click_pending = True
        if inp.mouse_left_held() and self._click_pending:
            if inp.mouse_dragging(self.DRAG_THRESHOLD_PX):
                self._panning = True
                self._click_pending = False
            if self._panning and inp.mouse_on_map(MAP_ORIGIN_Y):
                dx_px, dy_px = inp.mouse_delta()
                self._pan_accum_x -= dx_px / CELL_W
                self._pan_accum_y -= dy_px / CELL_H
                while abs(self._pan_accum_x) >= 1.0:
                    step = 1 if self._pan_accum_x > 0 else -1
                    ow.camera.pan_by(step, 0)
                    self._pan_accum_x -= step
                while abs(self._pan_accum_y) >= 1.0:
                    step = 1 if self._pan_accum_y > 0 else -1
                    ow.camera.pan_by(0, step)
                    self._pan_accum_y -= step
        if inp.mouse_left_released():
            if self._click_pending and not self._panning:
                world = inp.mouse_world(ow.camera, MAP_ORIGIN_Y)
                if world:
                    ow.interaction.try_examine_world(*world)
            self._panning = False
            self._click_pending = False

    def handle_input(self, inp) -> bool:
        ow = self.scene
        windows = ow.game.windows

        if ow.sheet and ow.sheet.visible:
            ow.sheet.bind_profile(ow.game.profile)
            if ow.sheet.handle_keys(inp):
                return False
            ow.sheet.handle_content_keys(inp, ow.game.profile, ow.examine)
            windows.handle_input(inp)
            return False

        if ow.craft and ow.craft.visible:
            ow.craft.bind(ow.game.profile, ow.game.world_state)
            if ow.craft.handle_keys(inp):
                return False
            ow.craft.handle_content_keys(
                inp, ow.game.profile, ow.game.world_state, ow.examine, ow.log, ow.game.audio
            )
            windows.handle_input(inp)
            return False

        if ow.examine and ow.examine.visible:
            if ow.examine.handle_keys(inp):
                return False
            windows.handle_input(inp)
            return False

        if windows.any_blocking_world():
            windows.handle_input(inp)
            if inp.pressed_escape():
                windows.close_topmost()
            return False

        if ow.dialogue_open:
            if inp.confirm_pressed() or inp.any_key_pressed() or inp.mouse_left_clicked():
                if ow.dialogue.advance():
                    ow.dialogue_open = False
            if inp.pressed(pygame.K_o):
                aid = {"elder_intro": "elder", "whisper_companion": "whisper_companion"}.get(
                    ow.dialogue_id, "elion"
                )
                ow.examine.show(aid)
            return False

        if windows.handle_input(inp):
            return False

        self._handle_map_mouse(inp)

        if inp.pressed(pygame.K_o):
            ow.interaction.try_examine_world(ow.player.x, ow.player.y)
            return False

        if inp.pressed_tab():
            ow.sheet.toggle()
            return False
        if inp.pressed_f5():
            save_game(ow.game.serialize_state())
            ow.log.add("Сохранено (F5).")
            return False
        if inp.pressed_f9():
            data = load_game()
            if data:
                ow.game.restore_state(data)
                ow.log.add("Загружено.")
            return False

        d = inp.dir_key()
        if d:
            ow.camera.reset_pan()
            nx, ny = ow.player.x + d[0], ow.player.y + d[1]
            layer = ow.game.world_state.layer
            if ow.game.world_map.is_walkable(nx, ny, layer):
                ch, _, _ = ow.game.world_map.get_tile(nx, ny, layer)
                if ch == ">":
                    ow.game.audio.play_sfx("stairs")
                    ow.game.request_scene("dungeon_enter")
                    return True
                if ch == "<":
                    ow.game.audio.play_sfx("stairs")
                    ow.game.request_scene("surface_exit")
                    return True
                ow.player.move(d[0], d[1])
                surface = resolve_footstep(nx, ny, layer, ow.game.world_map)
                ow.game.audio.play_footstep(surface)
                ow.game.world_state.turn_count += 1
                active, _ = ow.weather.on_turn(ow.fov.in_shelter())
                if active and layer == "surface":
                    ow.log.add("Пепельный ветер...")
                bid = ow.interaction.battle_for_tile(ch, nx, ny)
                if bid:
                    ow.pending_battle = bid
                    ow.game.world_state.defeated_battles.add((nx, ny, layer))

        if inp.pressed_e():
            ow.interaction.interact()
        return False
