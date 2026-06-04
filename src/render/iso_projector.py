"""World grid to screen character coordinates (2:1 isometric)."""
from __future__ import annotations

from src.constants import ISO_ORIGIN_X, ISO_ORIGIN_Y, ISO_STEP_X, ISO_STEP_Y


class IsoProjector:
    """Anchor (sx, sy) is the bottom tip of each tile footprint."""

    def __init__(
        self,
        origin_x: int = ISO_ORIGIN_X,
        origin_y: int = ISO_ORIGIN_Y,
        step_x: int = ISO_STEP_X,
        step_y: int = ISO_STEP_Y,
    ):
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.step_x = step_x
        self.step_y = step_y

    def world_to_screen(self, wx: int, wy: int) -> tuple[int, int]:
        sx = self.origin_x + (wx - wy) * self.step_x
        sy = self.origin_y + (wx + wy) * self.step_y
        return sx, sy

    def screen_to_world(
        self,
        sx: int,
        sy: int,
        wx0: int,
        wy0: int,
        view_w: int,
        view_h: int,
    ) -> tuple[int, int] | None:
        """Pick nearest tile anchor in the current view."""
        best: tuple[int, int] | None = None
        best_d2 = 10**9
        for vy in range(view_h):
            for vx in range(view_w):
                wx, wy = wx0 + vx, wy0 + vy
                ax, ay = self.world_to_screen(wx, wy)
                d2 = (sx - ax) ** 2 + (sy - ay) ** 2
                if d2 < best_d2:
                    best_d2 = d2
                    best = (wx, wy)
        if best_d2 > 36:
            return None
        return best

    def visible_tile_bounds(
        self, wx0: int, wy0: int, view_w: int, view_h: int
    ) -> tuple[int, int, int, int]:
        return wx0, wy0, wx0 + view_w, wy0 + view_h
