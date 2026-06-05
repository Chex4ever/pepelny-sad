"""Overworld map rendering (classic 1-char or isometric stencils)."""
from __future__ import annotations

import os

from src.constants import (
    COLOR_BG,
    COLOR_SURFACE_SKY,
    ENTITY_DRAW_Z_M,
    ISO_SKY_ROWS,
    MAP_ORIGIN_Y,
    MAP_VIEW_H,
    MAP_VIEW_W,
    SCREEN_H,
    SCREEN_W,
)
from src.render.iso_projector import IsoProjector
from src.render.light_map import LightMap
from src.render.render_mode import is_gpu, is_iso
from src.render.shadow_casters import gather_shadow_casters
from src.render.shadow_map import ShadowMap
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
from src.world.lighting import (
    ambient_for_time,
    ambient_for_turn,
    sky_char,
    sun_shadow_vector,
    torch_char,
    torch_flicker,
)
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, filter_tile_char, visibility_state

# Body center height for draw order (below tree canopy z_max, above trunks).
# ENTITY_DRAW_Z_M imported from src.constants


def _surface_shadows_enabled() -> bool:
    return os.environ.get("PEPELNY_SURFACE_SHADOWS", "0").strip().lower() not in (
        "0",
        "false",
        "no",
    )


class MapRenderer:
    def __init__(self, scene):
        self.scene = scene
        self._projector = IsoProjector()
        self._last_iso_queue: list[tuple] = []
        self._queue_cache_key: tuple | None = None
        self._cached_queue: list[tuple] = []

    def invalidate_queue_cache(self) -> None:
        self._queue_cache_key = None

    @property
    def last_iso_draw_queue(self) -> list[tuple]:
        return self._last_iso_queue

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
        ptx, pty = ow.player.tile_pos()
        px = int(round(ow.player.x)) - wx0
        py = int(round(ow.player.y)) - wy0
        profile = ow.game.profile.combat_profile()
        if profile.lantern:
            lm.add_source(px, py, 5.0, 0.45)
        if "sorrow_companion" in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ptx, pty)
            lm.add_source(cx - wx0, cy - wy0, 3.0, 0.25)
        if layer == "dungeon":
            lm.blur_3x3()
        return lm

    def build_shadow_map(
        self,
        wx0: int,
        wy0: int,
        wx_lo: int,
        wx_hi: int,
        wy_lo: int,
        wy_hi: int,
    ) -> ShadowMap:
        ow = self.scene
        vw, vh = map_view_w(), map_view_h()
        sm = ShadowMap(vw, vh)
        layer = ow.game.world_state.layer
        turn = int(ow.game.world_state.world_time_s)
        sdx, sdy, length_scale = sun_shadow_vector(turn, layer)
        companion_positions: list[tuple[int, int]] = []
        ptx, pty = ow.player.tile_pos()
        if ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ptx, pty)
            if (cx, cy) in ow.visible:
                companion_positions.append((cx, cy))
        casters = gather_shadow_casters(
            ow.game.world_map,
            layer,
            wx0,
            wy0,
            wx_lo,
            wx_hi,
            wy_lo,
            wy_hi,
            visible=ow.visible,
            is_explored=ow._is_explored,
            player_pos=(ptx, pty),
            companion_positions=companion_positions,
        )
        sm.apply_all(casters, sdx, sdy, length_scale=length_scale)
        return sm

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
        ambient = ambient_for_time(ow.game.world_state.world_time_s, layer, weather_dim)
        turn_vis = int(ow.game.world_state.world_time_s)

        self._draw_sky(buf, layer, turn_vis, ambient)

        light_map = self.build_light_map(wx0, wy0, ambient)
        shadow_map = self.build_shadow_map(
            wx0,
            wy0,
            wx0,
            wx0 + MAP_VIEW_W - 1,
            wy0,
            wy0 + MAP_VIEW_H - 1,
        )

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

                light = light_map.get(vx, vy) * shadow_map.get(vx, vy)
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

        ptx, pty = ow.player.tile_pos()
        px = int(round(ow.player.x)) - wx0
        py = int(round(ow.player.y)) - wy0 + MAP_ORIGIN_Y
        if 0 <= px < MAP_VIEW_W and 0 <= py < MAP_VIEW_H + MAP_ORIGIN_Y:
            buf.set(px, py, "@", fg=(255, 220, 120), light=1.0)

        for cid in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ptx, pty)
            if (cx, cy) not in ow.visible:
                continue
            cpx, cpy = cx - wx0, cy - wy0 + MAP_ORIGIN_Y
            sym = "~" if "whisper" in cid else "*"
            if 0 <= cpx < MAP_VIEW_W and 0 <= cpy < MAP_VIEW_H + MAP_ORIGIN_Y:
                buf.set(cpx, cpy, sym, fg=(150, 200, 180), light=1.0)

    def build_iso_draw_queue(
        self,
        wx0: int,
        wy0: int,
        *,
        light_map: LightMap | None = None,
        shadow_map: ShadowMap | None = None,
        ambient: float | None = None,
    ) -> list[tuple]:
        """sort_key, wx, wy, z_m, stencil_id, fg, bg, light, fog"""
        ow = self.scene
        layer = ow.game.world_state.layer
        vw, vh = map_view_w(), map_view_h()
        if light_map is None:
            if ambient is None:
                weather_dim = ow.weather.ambient_penalty() if layer == "surface" else 0
                ambient = ambient_for_time(ow.game.world_state.world_time_s, layer, weather_dim)
            light_map = self.build_light_map(wx0, wy0, ambient)

        projector = self._projector
        focus_wx, focus_wy = projector.view_focus(wx0, wy0, vw, vh)
        wm = ow.game.world_map
        wx_lo, wx_hi, wy_lo, wy_hi = projector.world_bounds_for_focus(focus_wx, focus_wy)
        if shadow_map is None:
            shadow_map = self.build_shadow_map(
                wx0, wy0, wx_lo, wx_hi, wy_lo, wy_hi
            )
        draw_queue: list[tuple] = []

        screen_margin = 8
        for wx in range(wx_lo, wx_hi + 1):
            for wy in range(wy_lo, wy_hi + 1):
                state = visibility_state(wx, wy, ow.visible, ow._is_explored)
                if state == UNEXPLORED:
                    continue
                sax, say = projector.world_to_screen(
                    wx, wy, focus_wx=focus_wx, focus_wy=focus_wy
                )
                if (
                    sax < -screen_margin
                    or say < -screen_margin
                    or sax > SCREEN_W + screen_margin
                    or say > SCREEN_H + screen_margin
                ):
                    continue
                vx, vy = wx - wx0, wy - wy0
                light = light_map.get(vx, vy) if 0 <= vx < vw and 0 <= vy < vh else ambient or 0.5
                if 0 <= vx < vw and 0 <= vy < vh:
                    light *= shadow_map.get(vx, vy)
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
                    sid = solid.stencil_id
                    if "trunk" in sid:
                        z = col.floor_z + solid.z_min
                        sort_key = wx + wy + 120
                        sfg, sbg = (120, 85, 55), (35, 28, 20)
                    elif "canopy" in sid:
                        z = col.floor_z + solid.z_min
                        sort_key = wx + wy + int((col.floor_z + solid.z_max) * 10)
                        sfg, sbg = col.fg, col.bg
                    else:
                        z = col.floor_z + solid.z_min
                        sort_key = wx + wy + int(z * 10)
                        sfg, sbg = col.fg, col.bg
                    draw_queue.append(
                        (
                            sort_key,
                            wx,
                            wy,
                            z,
                            sid,
                            sfg,
                            sbg,
                            light,
                            fog,
                        )
                    )

        draw_queue.sort(key=lambda t: (t[0], t[3]))
        return draw_queue

    @staticmethod
    def _iso_draw_sort_key(wx: int, wy: int, z_m: float) -> int:
        return wx + wy + int(z_m * 10)

    def append_iso_entities(
        self,
        draw_queue: list[tuple],
        layer: str,
    ) -> None:
        """Insert player/companions into the sorted map queue (canopy can draw on top)."""
        ow = self.scene
        wm = ow.game.world_map
        ptx, pty = ow.player.tile_pos()
        rx, ry = ow.player.x, ow.player.y
        pz = wm.get_column(ptx, pty, layer).floor_z + ENTITY_DRAW_Z_M
        draw_queue.append(
            (
                self._iso_draw_sort_key(ptx, pty, pz),
                rx,
                ry,
                pz,
                "sprite:player",
                (255, 220, 120),
                (8, 8, 18),
                1.0,
                0,
            )
        )
        for cid in ow.game.world_state.companions:
            cx, cy = companion_pos_for_player(ptx, pty)
            if (cx, cy) not in ow.visible:
                continue
            cz = wm.get_column(cx, cy, layer).floor_z + ENTITY_DRAW_Z_M
            draw_queue.append(
                (
                    self._iso_draw_sort_key(cx, cy, cz),
                    cx,
                    cy,
                    cz,
                    "sprite:companion",
                    (150, 200, 180),
                    (8, 8, 18),
                    1.0,
                    0,
                )
            )
        draw_queue.sort(key=lambda t: (t[0], t[3]))

    def _stamp_iso_queue_item(
        self,
        buf,
        projector: IsoProjector,
        item: tuple,
        layer: str,
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> None:
        _, wx, wy, z_m, sid, fg, bg, light, fog = item
        ax, ay = projector.world_to_screen(
            wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy
        )
        if not buf.in_bounds(ax, ay):
            return
        if sid.startswith("sprite:"):
            stencil = load_sprite(sid.split(":", 1)[1])
        else:
            stencil = load_tile_stencil(sid)
        is_floor = layer == "surface" and z_m == 0.0 and not sid.startswith("sprite:")
        stamp(
            buf,
            ax,
            ay,
            stencil,
            fg=fg,
            bg=bg,
            light=light,
            fog=fog,
            fill_iso_footprint=is_floor,
        )

    def _stamp_iso_fog(
        self,
        buf,
        wx0: int,
        wy0: int,
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> None:
        ow = self.scene
        projector = self._projector
        wx_lo, wx_hi, wy_lo, wy_hi = projector.world_bounds_for_focus(focus_wx, focus_wy)
        for wx in range(wx_lo, wx_hi + 1):
            for wy in range(wy_lo, wy_hi + 1):
                state = visibility_state(wx, wy, ow.visible, ow._is_explored)
                if state != UNEXPLORED:
                    continue
                ax, ay = projector.world_to_screen(
                    wx, wy, focus_wx=focus_wx, focus_wy=focus_wy
                )
                if not buf.in_bounds(ax, ay):
                    continue
                buf.set_fog(ax, ay, FOG_UNEXPLORED)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if buf.in_bounds(ax + dx, ay + dy):
                        buf.set_fog(ax + dx, ay + dy, FOG_UNEXPLORED)

    def iso_entity_draw_list(self, layer: str, focus_wx: int, focus_wy: int) -> list[tuple]:
        """Legacy hook for GPU path; entities are merged into last_iso_draw_queue."""
        _ = layer, focus_wx, focus_wy
        return []

    def _queue_cache_signature(
        self,
        wx0: int,
        wy0: int,
        focus_wx: int,
        focus_wy: int,
        ambient: float,
    ) -> tuple:
        ow = self.scene
        ws = ow.game.world_state
        ptx, pty = ow.player.tile_pos()
        return (
            wx0,
            wy0,
            focus_wx,
            focus_wy,
            ws.layer,
            ow.fov.visible_version,
            ptx,
            pty,
            ow.camera.pan_x,
            ow.camera.pan_y,
            int(ambient * 100),
            ow.game.world_map.chunks_loaded_version(),
            ow.frame,
        )

    def _draw_iso(self, buf, wx0: int, wy0: int) -> None:
        ow = self.scene
        if is_gpu():
            buf.clear(bg_a=0, fg_a=0)
        else:
            buf.clear(bg=COLOR_BG)
        layer = ow.game.world_state.layer
        weather_dim = ow.weather.ambient_penalty() if layer == "surface" else 0
        ambient = ambient_for_time(ow.game.world_state.world_time_s, layer, weather_dim)
        turn_vis = int(ow.game.world_state.world_time_s)

        self._draw_sky(buf, layer, turn_vis, ambient)

        vw, vh = map_view_w(), map_view_h()
        perf = self._perf()
        projector = self._projector
        focus_wx, focus_wy = projector.view_focus(wx0, wy0, vw, vh)
        wx_lo, wx_hi, wy_lo, wy_hi = projector.world_bounds_for_focus(focus_wx, focus_wy)
        with perf.measure("map_light"):
            light_map = self.build_light_map(wx0, wy0, ambient)
        with perf.measure("map_shadow"):
            if layer == "surface" and not _surface_shadows_enabled():
                shadow_map = ShadowMap(vw, vh)
            else:
                shadow_map = self.build_shadow_map(
                    wx0, wy0, wx_lo, wx_hi, wy_lo, wy_hi
                )

        sig = self._queue_cache_signature(wx0, wy0, focus_wx, focus_wy, ambient)
        if sig == self._queue_cache_key and self._cached_queue:
            draw_queue = self._cached_queue
            perf.counter("draw_queue_cache_hit")
        else:
            with perf.measure("map_queue"):
                draw_queue = self.build_iso_draw_queue(
                    wx0,
                    wy0,
                    light_map=light_map,
                    shadow_map=shadow_map,
                    ambient=ambient,
                )
                self.append_iso_entities(draw_queue, layer)
            self._cached_queue = draw_queue
            self._queue_cache_key = sig
        self._last_iso_queue = draw_queue
        perf.counter("draw_queue", len(draw_queue))

        stamp_map = not is_gpu()
        if stamp_map:
            for item in draw_queue:
                self._stamp_iso_queue_item(
                    buf,
                    projector,
                    item,
                    layer,
                    focus_wx=focus_wx,
                    focus_wy=focus_wy,
                )
                self._perf().counter("stamp")

        with self._perf().measure("map_fog"):
            if not is_gpu():
                self._stamp_iso_fog(buf, wx0, wy0, focus_wx=focus_wx, focus_wy=focus_wy)
