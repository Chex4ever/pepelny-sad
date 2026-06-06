"""FOV and ambient updates for overworld."""

from __future__ import annotations

from src.constants import visible_los_radius_surface
from src.overworld.fov import cast_los_fov
from src.progression.modules import module_fov_bonus


class FovController:
    def __init__(self, scene):
        self.scene = scene
        self._last_visible: set[tuple[int, int]] | None = None
        self._dirty = True
        self._last_pos: tuple[int, int] | None = None
        self._last_radius: int | None = None
        self.visible_version = 0

    @property
    def last_visible(self) -> set[tuple[int, int]]:
        return self._last_visible if self._last_visible is not None else set()

    def is_dirty(self) -> bool:
        return self._dirty

    def needs_recompute(self) -> bool:
        if self._dirty or self._last_visible is None:
            return True
        ow = self.scene
        pos = ow.player.tile_pos()
        radius = self.fov_radius()
        return pos != self._last_pos or radius != self._last_radius

    def mark_dirty(self) -> None:
        self._dirty = True

    def in_shelter(self) -> bool:
        ow = self.scene
        tx, ty = ow.player.tile_pos()
        ch, _, _ = ow.game.world_map.get_tile(tx, ty, ow.game.world_state.layer)
        return ch in "l&@=" or abs(tx) < 20 and abs(ty) < 20

    def fov_radius(self) -> int:
        layer = self.scene.game.world_state.layer
        if layer == "surface":
            radius = visible_los_radius_surface()
            radius += module_fov_bonus(self.scene.game.profile.installed_modules)
            # Weather advances on tile enter (locomotion); do not tick every radius query.
            penalty = (
                2
                if self.scene.weather.active and not self.in_shelter()
                else 0
            )
            return max(16, radius - penalty)
        return 14

    def update(self, wx0: int, wy0: int) -> set[tuple[int, int]]:
        _ = wx0
        ow = self.scene
        perf = ow.game.perf
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        radius = self.fov_radius()
        px, py = ow.player.tile_pos()

        if not self._dirty and self._last_visible is not None:
            if (px, py) == self._last_pos and radius == self._last_radius:
                return self._last_visible

        wm.mark_explored(px, py, layer)

        if layer == "surface":
            blocks_fn = lambda x, y: wm.fast_blocks_los(x, y, layer)
        else:
            from src.world.visibility import blocks_los as char_blocks_los

            def blocks_fn(x, y):
                ch, _, _ = wm.get_tile(x, y, layer)
                return char_blocks_los(ch)

        with perf.measure("fov_los"):
            visible = cast_los_fov(px, py, radius, blocks_fn)

        with perf.measure("fov_mark"):
            prev = self._last_visible
            if prev is None:
                to_mark = visible
            else:
                to_mark = visible - prev
            self._last_visible = visible
            for wx, wy in to_mark:
                wm.mark_explored(wx, wy, layer)

        self._dirty = False
        self._last_pos = (px, py)
        self._last_radius = radius
        self.visible_version += 1
        return visible

    def update_ambient(self, visible: set[tuple[int, int]]) -> None:
        ow = self.scene
        perf = ow.game.perf
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        px, py = ow.player.tile_pos()

        def tile_ch(x, y):
            return wm.get_tile(x, y, layer)[0]

        with perf.measure("fov_ambient"):
            ow.game.ambient.update(
                layer=layer,
                weather_active=ow.weather.active,
                in_shelter=self.in_shelter(),
                visible=visible,
                player_pos=(px, py),
                turn_count=ow.game.world_state.turn_count,
                tile_ch=tile_ch,
            )
