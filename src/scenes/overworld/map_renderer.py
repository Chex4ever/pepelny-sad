"""Overworld map rendering (classic 1-char or isometric stencils)."""
from __future__ import annotations

from src.constants import (
    COLOR_BG,
    COLOR_SURFACE_SKY,
    ISO_ORIGIN_X,
    ISO_ORIGIN_Y,
    ISO_SKY_ROWS,
    MAP_ORIGIN_Y,
    MAP_VIEW_H,
    MAP_VIEW_W,
    SCREEN_W,
)
from src.render.iso_projector import IsoProjector
from src.render.light_map import LightMap
from src.render.render_mode import is_iso
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED
from src.render.tile_stencil import (
    load_sprite,
    load_tile_stencil,
    stamp,
    stencil_id_for_char,
)
from src.render.viewport import map_view_h, map_view_w
from src.world.companions import companion_pos_for_player, has_service
from src.world.dungeon_reskin import reskin_char
from src.world.lighting import ambient_for_turn, sky_char, torch_char, torch_flicker
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, filter_tile_char, visibility_state


class MapRenderer:
    def __init__(self, scene):
        self.scene = scene
        self._projector = IsoProjector()

    def build_light_map(self, wx0: int, wy0: int, ambient: float) -> LightMap:
        ow = self.scene
        vw, vh = map_view_w(), map_view_h()
        lm = LightMap(vw, vh)
        lm.clear(ambient)
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        for vy in range(vh):
            for vx in range(vw):
                wx, wy = wx0 + vx, wy0 + vy
                if layer == "dungeon":
                    ch, _, _ = wm.get_tile(wx, wy, layer)
                else:
                    cx, cy, lx, ly = wm.world_to_chunk(wx, wy)
                    chunk = wm.chunks.get((cx, cy))
                    ch = chunk.get(lx, ly) if chunk and chunk.in_bounds(lx, ly) else "."
                if ch in "li":
                    lm.add_source(vx, vy, 4.5, 0.55)
        px = ow.player.x - wx0
        py = ow.player.y - wy0
        profile = ow.game.profile.combat_profile()
        if profile.lantern:
            lm.add_source(px, py, 5.0, 0.45)
        if "sorrow_companion" in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ow.player.x, ow.player.y)
            lm.add_source(cx - wx0, cy - wy0, 3.0, 0.25)
        if layer == "dungeon":
            lm.blur_3x3()
        return lm

    def draw(self, buf, wx0: int, wy0: int) -> None:
        if is_iso():
            self._draw_iso(buf, wx0, wy0)
        else:
            self._draw_classic(buf, wx0, wy0)

    def _perf(self):
        return self.scene.game.perf

    def _draw_sky(self, buf, layer: str, turn_count: int, ambient: float) -> None:
        if layer != "surface":
            return
        sky = sky_char(turn_count)
        sky_h = ISO_SKY_ROWS if is_iso() else 1
        for y in range(sky_h):
            for x in range(SCREEN_W):
                buf.set(x, y, sky, fg=(180, 180, 200), bg=COLOR_SURFACE_SKY, light=ambient)

    def _draw_classic(self, buf, wx0: int, wy0: int) -> None:
        ow = self.scene
        buf.clear(bg=COLOR_BG)
        layer = ow.game.world_state.layer
        weather_dim = ow.weather.ambient_penalty() if layer == "surface" else 0
        ambient = ambient_for_turn(ow.game.world_state.turn_count, layer, weather_dim)

        self._draw_sky(buf, layer, ow.game.world_state.turn_count, ambient)

        light_map = self.build_light_map(wx0, wy0, ambient)

        for vy in range(MAP_VIEW_H):
            for vx in range(MAP_VIEW_W):
                wx, wy = wx0 + vx, wy0 + vy
                state = visibility_state(wx, wy, ow.visible, ow._is_explored)
                if state == UNEXPLORED:
                    buf.set_fog(vx, vy + MAP_ORIGIN_Y, FOG_UNEXPLORED)
                    continue

                ch, fg, bg = ow.game.world_map.get_tile(wx, wy, layer)
                if layer == "dungeon":
                    ch, override = reskin_char(
                        ch, ow.game.world_state.spare_count, ow.game.world_state.kill_count
                    )
                    if override:
                        fg = override
                ch = filter_tile_char(ch, state)
                if ch is None:
                    buf.set_fog(vx, vy + MAP_ORIGIN_Y, FOG_UNEXPLORED)
                    continue

                light = light_map.get(vx, vy)
                if ch in "li":
                    light *= torch_flicker(ow.frame, wx + wy)
                    ch = torch_char(ow.frame)
                fog = FOG_EXPLORED if state == EXPLORED else 0
                if fog:
                    buf.set_fog(vx, vy + MAP_ORIGIN_Y, fog)
                if has_service(ow.game.world_state.companions, "shard_ping") and ch == "*" and state == VISIBLE:
                    light = max(light, 1.2)
                buf.set(vx, vy + MAP_ORIGIN_Y, ch, fg=fg, bg=bg, light=light)

        light_map.apply_to_buffer(buf, 0, MAP_ORIGIN_Y)

        px = ow.player.x - wx0
        py = ow.player.y - wy0 + MAP_ORIGIN_Y
        if 0 <= px < MAP_VIEW_W and 0 <= py < MAP_VIEW_H + MAP_ORIGIN_Y:
            buf.set(px, py, "@", fg=(255, 220, 120), light=1.0)

        for cid in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ow.player.x, ow.player.y)
            if (cx, cy) not in ow.visible:
                continue
            cpx, cpy = cx - wx0, cy - wy0 + MAP_ORIGIN_Y
            sym = "~" if "whisper" in cid else "*"
            if 0 <= cpx < MAP_VIEW_W and 0 <= cpy < MAP_VIEW_H + MAP_ORIGIN_Y:
                buf.set(cpx, cpy, sym, fg=(150, 200, 180), light=1.0)

    def _draw_iso(self, buf, wx0: int, wy0: int) -> None:
        ow = self.scene
        buf.clear(bg=COLOR_BG)
        layer = ow.game.world_state.layer
        weather_dim = ow.weather.ambient_penalty() if layer == "surface" else 0
        ambient = ambient_for_turn(ow.game.world_state.turn_count, layer, weather_dim)

        self._draw_sky(buf, layer, ow.game.world_state.turn_count, ambient)

        vw, vh = map_view_w(), map_view_h()
        light_map = self.build_light_map(wx0, wy0, ambient)
        projector = self._projector
        wm = ow.game.world_map

        # sort_key, wx, wy, z_m, stencil_id, fg, bg, light, fog
        draw_queue: list[tuple] = []

        for vy in range(vh):
            for vx in range(vw):
                wx, wy = wx0 + vx, wy0 + vy
                state = visibility_state(wx, wy, ow.visible, ow._is_explored)
                if state == UNEXPLORED:
                    continue
                light = light_map.get(vx, vy)
                fog = FOG_EXPLORED if state == EXPLORED else 0

                if layer == "dungeon":
                    ch, fg, bg = wm.get_tile(wx, wy, layer)
                    ch, override = reskin_char(
                        ch, ow.game.world_state.spare_count, ow.game.world_state.kill_count
                    )
                    if override:
                        fg = override
                    ch = filter_tile_char(ch, state)
                    if ch is None:
                        continue
                    if ch in "li":
                        light *= torch_flicker(ow.frame, wx + wy)
                    sid = stencil_id_for_char(ch, layer, fg, bg)
                    draw_queue.append((wx + wy, wx, wy, 0.0, sid, fg, bg, light, fog))
                    continue

                col = wm.get_column(wx, wy, layer)
                draw_queue.append(
                    (
                        wx + wy,
                        wx,
                        wy,
                        col.floor_z,
                        col.floor_stencil_id,
                        col.fg,
                        col.bg,
                        light,
                        fog,
                    )
                )
                for solid in col.solids:
                    if not solid.stencil_id:
                        continue
                    z = col.floor_z + solid.z_min
                    draw_queue.append(
                        (
                            wx + wy + int(z * 10),
                            wx,
                            wy,
                            z,
                            solid.stencil_id,
                            col.fg,
                            col.bg,
                            light,
                            fog,
                        )
                    )

        self._perf().counter("draw_queue", len(draw_queue))
        draw_queue.sort(key=lambda t: (t[0], t[3]))

        for _, wx, wy, z_m, sid, fg, bg, light, fog in draw_queue:
            ax, ay = projector.world_to_screen(wx, wy, z_m)
            if not buf.in_bounds(ax, ay):
                continue
            stencil = load_tile_stencil(sid)
            stamp(buf, ax, ay, stencil, fg=fg, bg=bg, light=light, fog=fog)
            self._perf().counter("stamp")

        for vy in range(vh):
            for vx in range(vw):
                wx, wy = wx0 + vx, wy0 + vy
                if visibility_state(wx, wy, ow.visible, ow._is_explored) != UNEXPLORED:
                    continue
                ax, ay = projector.world_to_screen(wx, wy)
                buf.set_fog(ax, ay, FOG_UNEXPLORED)
                buf.set_fog(ax + 1, ay, FOG_UNEXPLORED)
                buf.set_fog(ax - 1, ay, FOG_UNEXPLORED)
                buf.set_fog(ax, ay - 1, FOG_UNEXPLORED)

        pz = wm.get_column(ow.player.x, ow.player.y, layer).floor_z
        pax, pay = projector.world_to_screen(ow.player.x, ow.player.y, pz)
        stamp(buf, pax, pay, load_sprite("player"), light=1.0)

        for cid in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ow.player.x, ow.player.y)
            if (cx, cy) not in ow.visible:
                continue
            cz = wm.get_column(cx, cy, layer).floor_z
            cax, cay = projector.world_to_screen(cx, cy, cz)
            stamp(buf, cax, cay, load_sprite("companion"), fg=(150, 200, 180), light=1.0)
