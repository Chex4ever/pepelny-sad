"""Overworld input routing."""
from __future__ import annotations

import pygame

from src.audio.tile_sounds import resolve_footstep
from src.constants import MAP_ORIGIN_Y
from src.render.viewport import map_pan_cell_h, map_pan_cell_w
from src.world.companions import companion_pos_for_player
from src.world.save import load_game, save_game
from src.world.tile_entities import resolve_companion, resolve_player, resolve_world_cell
from src.i18n import t
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, visibility_state


class OverworldInputRouter:
    DRAG_THRESHOLD_PX = 10

    def __init__(self, scene):
        self.scene = scene
        self._panning = False
        self._click_pending = False
        self._drag_start = (0, 0)
        self._pan_base = (0, 0)
        self._mmb_panning = False

    def update_mouse_tooltip(self, inp) -> None:
        ow = self.scene
        world = inp.mouse_world(ow.camera, MAP_ORIGIN_Y)
        if world is None:
            ow.status.set_tooltip("")
            return
        wx, wy = world
        state = visibility_state(wx, wy, ow.visible, ow._is_explored)
        if state == UNEXPLORED:
            ow.status.set_tooltip(t("ui.status.unknown_land"))
            return
        if (wx, wy) == (ow.player.x, ow.player.y):
            name, _ = resolve_player()
            ow.status.set_tooltip(f"{name} (Tab)", can_examine=True)
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
            ow.status.set_tooltip(t("ui.status.memory_place"), can_examine=False)
        else:
            ow.status.set_tooltip("")

    def _begin_pan(self, inp) -> None:
        ow = self.scene
        self._panning = True
        self._click_pending = False
        self._drag_start = inp.mouse_pos
        self._pan_base = (ow.camera.pan_x, ow.camera.pan_y)

    def _apply_pan_drag(self, inp) -> None:
        ow = self.scene
        total_dx = inp.mouse_pos[0] - self._drag_start[0]
        total_dy = inp.mouse_pos[1] - self._drag_start[1]
        ow.camera.pan_from_drag(
            total_dx,
            total_dy,
            map_pan_cell_w(),
            map_pan_cell_h(),
            self._pan_base[0],
            self._pan_base[1],
        )

    def _pointer_over_window(self, inp) -> bool:
        gx, gy = inp.mouse_grid()
        return self.scene.game.windows.pointer_over_visible(gx, gy)

    def _handle_map_mouse(self, inp) -> None:
        ow = self.scene

        if inp.mouse_middle_down() and inp.mouse_on_map(MAP_ORIGIN_Y) and not self._pointer_over_window(inp):
            self._mmb_panning = True
            self._begin_pan(inp)

        if inp.mouse_left_down():
            if inp.mouse_on_map(MAP_ORIGIN_Y) and not self._pointer_over_window(inp):
                self._panning = False
                self._click_pending = True
                self._drag_start = inp.mouse_pos
                self._pan_base = (ow.camera.pan_x, ow.camera.pan_y)

        if inp.mouse_middle_held() and self._mmb_panning:
            self._apply_pan_drag(inp)
        elif inp.mouse_left_held() and self._click_pending:
            if inp.mouse_dragging(self.DRAG_THRESHOLD_PX):
                self._begin_pan(inp)
            if self._panning:
                self._apply_pan_drag(inp)

        if inp.mouse_left_released():
            if self._click_pending and not self._panning and not self._pointer_over_window(inp):
                world = inp.mouse_world(ow.camera, MAP_ORIGIN_Y)
                if world:
                    ow.interaction.try_examine_world(*world)
            self._panning = False
            self._click_pending = False

        if inp.mouse_middle_released():
            self._mmb_panning = False

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

        self._handle_map_mouse(inp)
        windows.handle_input(inp)

        if inp.pressed(pygame.K_o):
            ow.interaction.try_examine_world(ow.player.x, ow.player.y)
            return False

        if inp.pressed_tab():
            ow.sheet.show()
            ow.sheet.bind_profile(ow.game.profile)
            if getattr(ow.game, "tutorial", None):
                ow.game.tutorial.notify_sheet_opened()
            return False

        if inp.pressed(pygame.K_r) and ow.camera.is_panned():
            ow.camera.reset_pan()
            ow.game.audio.play_sfx("ui_confirm")
            return False

        if inp.pressed_f5():
            save_game(ow.game.serialize_state())
            ow.log.add(t("ui.log.saved_f5"))
            return False
        if inp.pressed_f9():
            data = load_game()
            if data:
                ow.game.restore_state(data)
                log = ow.game.windows.get("log")
                if log:
                    log.show()
                ow.log.add(t("ui.log.loaded"))
            return False

        d = inp.dir_key()
        if d:
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
                if getattr(ow.game, "tutorial", None):
                    ow.game.tutorial.notify_moved()
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
