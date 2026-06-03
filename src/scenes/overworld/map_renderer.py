"""Overworld map rendering."""
from __future__ import annotations

from src.constants import COLOR_BG, COLOR_SURFACE_SKY, MAP_ORIGIN_Y, MAP_VIEW_H, MAP_VIEW_W
from src.render.light_map import LightMap
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED
from src.world.companions import companion_pos_for_player, has_service
from src.world.dungeon_reskin import reskin_char
from src.world.lighting import ambient_for_turn, sky_char, torch_char, torch_flicker
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, filter_tile_char, visibility_state


class MapRenderer:
    def __init__(self, scene):
        self.scene = scene

    def build_light_map(self, wx0: int, wy0: int, ambient: float) -> LightMap:
        ow = self.scene
        lm = LightMap(MAP_VIEW_W, MAP_VIEW_H)
        lm.clear(ambient)
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        for vy in range(MAP_VIEW_H):
            for vx in range(MAP_VIEW_W):
                wx, wy = wx0 + vx, wy0 + vy
                ch, _, _ = wm.get_tile(wx, wy, layer)
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
        lm.blur_3x3()
        return lm

    def draw(self, buf, wx0: int, wy0: int) -> None:
        ow = self.scene
        buf.clear(bg=COLOR_BG)
        layer = ow.game.world_state.layer
        weather_dim = ow.weather.ambient_penalty() if layer == "surface" else 0
        ambient = ambient_for_turn(ow.game.world_state.turn_count, layer, weather_dim)

        if layer == "surface":
            sky = sky_char(ow.game.world_state.turn_count)
            for x in range(MAP_VIEW_W):
                buf.set(x, 0, sky, fg=(180, 180, 200), bg=COLOR_SURFACE_SKY, light=ambient)

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
                if state == EXPLORED:
                    buf.set_fog(vx, vy + MAP_ORIGIN_Y, FOG_EXPLORED)
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
