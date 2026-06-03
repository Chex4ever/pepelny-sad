"""Main overworld exploration scene."""
from __future__ import annotations

import pygame

from src.constants import MAP_VIEW_H, MAP_VIEW_W, SCREEN_H, SCREEN_W
from src.overworld.fov import cast_los_fov
from src.overworld.player import OverworldPlayer
from src.render.light_map import LightMap
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED
from src.story.dialogues import get_dialogue
from src.ui.character_sheet import CharacterSheet
from src.ui.craft_station import CraftStation
from src.ui.examine_panel import ExaminePanel
from src.ui.log_panel import LogPanel
from src.ui.tooltip import Tooltip
from src.world.companions import companion_pos_for_player, has_service
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.lighting import ambient_for_turn, sky_char, torch_char, torch_flicker
from src.world.pepel_weather import PepelWeather
from src.world.save import load_game, save_game
from src.world.tile_entities import resolve_companion, resolve_player, resolve_world_cell
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, filter_tile_char, visibility_state


class OverworldScene:
    MAP_ORIGIN_Y = 1

    def __init__(self, game):
        self.game = game
        self.player = OverworldPlayer(x=20, y=24)
        self.log = LogPanel()
        self.sheet = CharacterSheet()
        self.craft = CraftStation()
        self.examine = ExaminePanel()
        self.tooltip = Tooltip()
        self.weather = PepelWeather(game.world_state.world_seed)
        self.dialogue_lines: list[str] = []
        self.dialogue_idx = 0
        self.dialogue_open = False
        self.dialogue_id = ""
        self.pending_battle: str | None = None
        self.frame = 0
        self.visible: set[tuple[int, int]] = set()
        self._camera = (0, 0)
        if game.world_state.layer == "dungeon":
            ensure_dungeon(game.world_state, game.world_map)
            self.player.x, self.player.y = 2, 2

    def _in_shelter(self) -> bool:
        ch, _, _ = self.game.world_map.get_tile(self.player.x, self.player.y, self.game.world_state.layer)
        return ch in "l&@=" or abs(self.player.x) < 20 and abs(self.player.y) < 20

    def _fov_radius(self) -> int:
        layer = self.game.world_state.layer
        if layer == "surface":
            return max(MAP_VIEW_W, MAP_VIEW_H) + 4
        return 14

    def update(self):
        self.frame += 1
        layer = self.game.world_state.layer
        wx0 = self.player.x - MAP_VIEW_W // 2
        wy0 = self.player.y - MAP_VIEW_H // 2
        self._camera = (wx0, wy0)
        radius = self._fov_radius()

        wm = self.game.world_map

        def tile_ch(x, y):
            return wm.get_tile(x, y, layer)[0]

        self.visible = cast_los_fov(
            self.player.x,
            self.player.y,
            radius,
            tile_ch,
            min_x=wx0 - 1,
            max_x=wx0 + MAP_VIEW_W,
            min_y=wy0 - 1,
            max_y=wy0 + MAP_VIEW_H,
        )
        for wx, wy in self.visible:
            wm.mark_explored(wx, wy, layer)

    def _is_explored(self, wx: int, wy: int) -> bool:
        return self.game.world_map.is_explored(wx, wy, self.game.world_state.layer)

    def _battle_for_tile(self, ch: str, wx: int, wy: int) -> str | None:
        if ch != "!":
            return None
        key = (wx, wy, self.game.world_state.layer)
        if key in self.game.world_state.defeated_battles:
            return None
        if self.game.world_state.layer == "dungeon":
            return "warden" if self.game.world_state.dungeon_entered else "sorrow"
        if wy > 30:
            return "sorrow"
        if abs(wx) > 40:
            return "whisper"
        return "whisper"

    def _try_examine_world(self, wx: int, wy: int):
        if (wx, wy) not in self.visible:
            return
        info = resolve_world_cell(wx, wy, self.game.world_state.layer, self.game)
        if info:
            _, art_id = info
            self.examine.show(art_id)

    def _update_mouse(self, inp):
        wx0, wy0 = self._camera
        world = inp.mouse_world(wx0, wy0, self.MAP_ORIGIN_Y)
        if world is None:
            self.tooltip.clear()
            return
        wx, wy = world
        state = visibility_state(wx, wy, self.visible, self._is_explored)
        if state == UNEXPLORED:
            self.tooltip.set("Неизвестная земля", can_examine=False)
            return
        if (wx, wy) == (self.player.x, self.player.y):
            name, _ = resolve_player()
            self.tooltip.set(name)
            return
        for cid in self.game.world_state.companions:
            cx, cy = companion_pos_for_player(self.player.x, self.player.y)
            if (wx, wy) == (cx, cy):
                name, _ = resolve_companion(cid)
                self.tooltip.set(name)
                return
        info = resolve_world_cell(wx, wy, self.game.world_state.layer, self.game)
        if info and state == VISIBLE:
            name, _ = info
            self.tooltip.set(name)
        elif state == EXPLORED:
            self.tooltip.set("Память о месте", can_examine=False)
        else:
            self.tooltip.clear()

    def handle_input(self, inp):
        if self.examine.open:
            if inp.pressed(pygame.K_ESCAPE):
                self.examine.close()
            return False
        if self.dialogue_open:
            if inp.any_pressed(pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.dialogue_idx += 1
                if self.dialogue_idx >= len(self.dialogue_lines):
                    self.dialogue_open = False
            if inp.pressed(pygame.K_o):
                aid = {"elder_intro": "elder", "whisper_companion": "whisper_companion"}.get(
                    self.dialogue_id, "elion"
                )
                self.examine.show(aid)
            return False
        if self.sheet.handle_input(inp, self.game.profile, self.examine):
            return False
        if self.craft.handle_input(inp, self.game.profile, self.game.world_state, self.examine, self.log):
            return False

        if inp.mouse_left_clicked():
            wx0, wy0 = self._camera
            world = inp.mouse_world(wx0, wy0, self.MAP_ORIGIN_Y)
            if world:
                self._try_examine_world(*world)

        if inp.pressed(pygame.K_o):
            self._try_examine_world(self.player.x, self.player.y)
            return False

        if inp.pressed(pygame.K_TAB):
            self.sheet.open = not self.sheet.open
            return False
        if inp.pressed(pygame.K_F5):
            self._save_checkpoint()
            self.log.add("Сохранено (F5).")
            return False
        if inp.pressed(pygame.K_F9):
            data = load_game()
            if data:
                self.game.restore_state(data)
                self.log.add("Загружено.")
            return False

        d = inp.dir_key()
        if d:
            nx, ny = self.player.x + d[0], self.player.y + d[1]
            layer = self.game.world_state.layer
            if self.game.world_map.is_walkable(nx, ny, layer):
                ch, _, _ = self.game.world_map.get_tile(nx, ny, layer)
                if ch == ">":
                    self.game.request_scene("dungeon_enter")
                    return True
                if ch == "<":
                    self.game.request_scene("surface_exit")
                    return True
                self.player.move(d[0], d[1])
                self.game.world_state.turn_count += 1
                active, _ = self.weather.on_turn(self._in_shelter())
                if active and layer == "surface":
                    self.log.add("Пепельный ветер...")
                bid = self._battle_for_tile(ch, nx, ny)
                if bid:
                    self.pending_battle = bid
                    self.game.world_state.defeated_battles.add((nx, ny, layer))

        if inp.pressed(pygame.K_e):
            self._interact()
        return False

    def _interact(self):
        layer = self.game.world_state.layer
        px, py = self.player.x, self.player.y
        for dx, dy in [(0, 0), self.player.facing, (1, 0), (-1, 0), (0, 1), (0, -1)]:
            tx, ty = px + dx, py + dy
            ch, _, _ = self.game.world_map.get_tile(tx, ty, layer)
            if ch == "o":
                active, _ = self.weather.on_turn(self._in_shelter())
                if active and layer == "surface" and not self._in_shelter():
                    self.log.add("Пепельный ветер — трава недоступна.")
                    return
                self.game.profile.inventory.add("grey_herb", 1, 20)
                self._clear_tile(tx, ty, layer)
                self.log.add("Собрана серая трава.")
                return
            if ch == "+":
                self.game.profile.inventory.add("root_fiber", 1, 20)
                self._clear_tile(tx, ty, layer)
                self.log.add("Собрано корневое волокно.")
                return
            if ch == "*":
                self.game.profile.inventory.add("star_shard", 1, 10)
                self._clear_tile(tx, ty, layer)
                self.log.add("Найден осколок звезды.")
                return
            if ch == "$":
                self.game.profile.inventory.add("ash_clump", 2, 30)
                self.log.add("Подобран пепел.")
                return
            if ch == "&":
                self.craft.open_station("forge")
                return
            if ch == "~":
                self.craft.open_station("loom")
                return
            if ch == "@":
                self._open_dialogue("elder_intro")
                return
        if has_service(self.game.world_state.companions, "mobile_forge"):
            cx, cy = companion_pos_for_player(px, py)
            if abs(cx - px) + abs(cy - py) <= 2:
                self.craft.open_station("companion")
                self._open_dialogue("whisper_companion")
                return
        if "sorrow_companion" in self.game.world_state.companions:
            self.log.add("Осколки мерцают вдали...")

    def _clear_tile(self, tx: int, ty: int, layer: str):
        if layer == "dungeon":
            self.game.world_map.set_dungeon_tile(tx, ty, ".")
        else:
            cx, cy, lx, ly = self.game.world_map.world_to_chunk(tx, ty)
            chunk = self.game.world_map.chunks.get((cx, cy))
            if chunk:
                chunk.set(lx, ly, ".")

    def _open_dialogue(self, did: str):
        self.dialogue_id = did
        self.dialogue_lines = get_dialogue(did)
        self.dialogue_idx = 0
        self.dialogue_open = True

    def _save_checkpoint(self):
        save_game(self.game.serialize_state())

    def _build_light_map(self, wx0, wy0, ambient: float) -> LightMap:
        lm = LightMap(MAP_VIEW_W, MAP_VIEW_H)
        lm.clear(ambient)
        layer = self.game.world_state.layer
        wm = self.game.world_map
        for vy in range(MAP_VIEW_H):
            for vx in range(MAP_VIEW_W):
                wx, wy = wx0 + vx, wy0 + vy
                ch, _, _ = wm.get_tile(wx, wy, layer)
                if ch in "li":
                    lm.add_source(vx, vy, 4.5, 0.55)
        px = self.player.x - wx0
        py = self.player.y - wy0
        profile = self.game.profile.combat_profile()
        if profile.lantern:
            lm.add_source(px, py, 5.0, 0.45)
        if "sorrow_companion" in self.game.world_state.companions:
            cx, cy = companion_pos_for_player(self.player.x, self.player.y)
            lm.add_source(cx - wx0, cy - wy0, 3.0, 0.25)
        lm.blur_3x3()
        return lm

    def draw(self, buf, inp=None):
        from src.constants import COLOR_BG, COLOR_SURFACE_SKY, COLOR_TEXT
        from src.world.dungeon_reskin import reskin_char

        if inp:
            self._update_mouse(inp)

        buf.clear(bg=COLOR_BG)
        layer = self.game.world_state.layer
        wx0, wy0 = self._camera
        weather_dim = self.weather.ambient_penalty() if layer == "surface" else 0
        ambient = ambient_for_turn(self.game.world_state.turn_count, layer, weather_dim)

        if layer == "surface":
            sky = sky_char(self.game.world_state.turn_count)
            for x in range(MAP_VIEW_W):
                buf.set(x, 0, sky, fg=(180, 180, 200), bg=COLOR_SURFACE_SKY, light=ambient)

        light_map = self._build_light_map(wx0, wy0, ambient)

        for vy in range(MAP_VIEW_H):
            for vx in range(MAP_VIEW_W):
                wx, wy = wx0 + vx, wy0 + vy
                state = visibility_state(wx, wy, self.visible, self._is_explored)
                if state == UNEXPLORED:
                    buf.set_fog(vx, vy + self.MAP_ORIGIN_Y, FOG_UNEXPLORED)
                    continue

                ch, fg, bg = self.game.world_map.get_tile(wx, wy, layer)
                if layer == "dungeon":
                    ch, override = reskin_char(ch, self.game.world_state.spare_count, self.game.world_state.kill_count)
                    if override:
                        fg = override
                ch = filter_tile_char(ch, state)
                if ch is None:
                    buf.set_fog(vx, vy + self.MAP_ORIGIN_Y, FOG_UNEXPLORED)
                    continue

                light = light_map.get(vx, vy)
                if ch in "li":
                    light *= torch_flicker(self.frame, wx + wy)
                    ch = torch_char(self.frame)
                if state == EXPLORED:
                    buf.set_fog(vx, vy + self.MAP_ORIGIN_Y, FOG_EXPLORED)
                if has_service(self.game.world_state.companions, "shard_ping") and ch == "*" and state == VISIBLE:
                    light = max(light, 1.2)
                buf.set(vx, vy + self.MAP_ORIGIN_Y, ch, fg=fg, bg=bg, light=light)

        light_map.apply_to_buffer(buf, 0, self.MAP_ORIGIN_Y)

        px = self.player.x - wx0
        py = self.player.y - wy0 + self.MAP_ORIGIN_Y
        if 0 <= px < MAP_VIEW_W and 0 <= py < MAP_VIEW_H + self.MAP_ORIGIN_Y:
            buf.set(px, py, "@", fg=(255, 220, 120), light=1.0)

        for cid in self.game.world_state.companions:
            cx, cy = companion_pos_for_player(self.player.x, self.player.y)
            if (cx, cy) not in self.visible:
                continue
            cpx, cpy = cx - wx0, cy - wy0 + self.MAP_ORIGIN_Y
            sym = "~" if "whisper" in cid else "*"
            if 0 <= cpx < MAP_VIEW_W and 0 <= cpy < MAP_VIEW_H + self.MAP_ORIGIN_Y:
                buf.set(cpx, cpy, sym, fg=(150, 200, 180), light=1.0)

        self.log.draw(buf, MAP_VIEW_W + 2, 1)
        buf.draw_text(2, SCREEN_H - 3, f"Layer:{layer} Turn:{self.game.world_state.turn_count}", fg=COLOR_TEXT)
        buf.draw_text(2, SCREEN_H - 2, "WASD E Tab F1 Esc | ЛКМ — осмотр", fg=COLOR_TEXT)

        self.sheet.draw(buf, self.game.profile)
        self.craft.draw(buf, self.game.profile, self.game.world_state, self.examine)
        self.examine.draw(buf)
        self.tooltip.draw(buf)

        if self.dialogue_open and self.dialogue_idx < len(self.dialogue_lines):
            buf.draw_box(10, SCREEN_H - 8, 70, 5, "ДИАЛОГ")
            buf.draw_text(12, SCREEN_H - 6, self.dialogue_lines[self.dialogue_idx][:66], fg=COLOR_TEXT)

    @property
    def needs_battle(self) -> str | None:
        b = self.pending_battle
        self.pending_battle = None
        return b
