"""FOV and ambient updates for overworld."""
from __future__ import annotations

from src.constants import MAP_VIEW_TILES_H, MAP_VIEW_TILES_W
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
            # World tiles in view (iso footprint); classic char grid is larger visually.
            return max(MAP_VIEW_TILES_W, MAP_VIEW_TILES_H) + 4
        return 14

    def update(self, wx0: int, wy0: int) -> set[tuple[int, int]]:
        ow = self.scene
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        radius = self.fov_radius()

        if layer == "surface":
            blocks_fn = lambda x, y: wm.fast_blocks_los(x, y, layer)
        else:
            from src.world.visibility import blocks_los as char_blocks_los

            def blocks_fn(x, y):
                ch, _, _ = wm.get_tile(x, y, layer)
                return char_blocks_los(ch)

        visible = cast_los_fov(
            ow.player.x,
            ow.player.y,
            radius,
            blocks_fn,
            min_x=wx0,
            max_x=wx0 + MAP_VIEW_TILES_W - 1,
            min_y=wy0,
            max_y=wy0 + MAP_VIEW_TILES_H - 1,
        )

        def tile_ch(x, y):
            return wm.get_tile(x, y, layer)[0]
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
