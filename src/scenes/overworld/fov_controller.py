"""FOV and ambient updates for overworld."""
from __future__ import annotations

from src.render.viewport import map_view_h, map_view_w
from src.overworld.fov import cast_los_fov


class FovController:
    def __init__(self, scene):
        self.scene = scene

    def in_shelter(self) -> bool:
        ow = self.scene
        ch, _, _ = ow.game.world_map.get_tile(
            ow.player.x, ow.player.y, ow.game.world_state.layer
        )
        return ch in "l&@=" or abs(ow.player.x) < 20 and abs(ow.player.y) < 20

    def fov_radius(self) -> int:
        layer = self.scene.game.world_state.layer
        if layer == "surface":
            return max(map_view_w(), map_view_h()) + 4
        return 14

    def update(self, wx0: int, wy0: int) -> set[tuple[int, int]]:
        ow = self.scene
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        radius = self.fov_radius()

        def tile_ch(x, y):
            return wm.get_tile(x, y, layer)[0]

        visible = cast_los_fov(
            ow.player.x,
            ow.player.y,
            radius,
            tile_ch,
            min_x=wx0 - 1,
            max_x=wx0 + map_view_w(),
            min_y=wy0 - 1,
            max_y=wy0 + map_view_h(),
        )
        for wx, wy in visible:
            wm.mark_explored(wx, wy, layer)

        ow.game.ambient.update(
            layer=layer,
            weather_active=ow.weather.active,
            in_shelter=self.in_shelter(),
            visible=visible,
            player_pos=(ow.player.x, ow.player.y),
            turn_count=ow.game.world_state.turn_count,
            tile_ch=tile_ch,
        )
        return visible
