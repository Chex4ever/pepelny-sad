"""World grid to screen character coordinates (2:1 isometric)."""
from __future__ import annotations

from src.constants import (
    ISO_ORIGIN_X,
    ISO_ORIGIN_Y,
    ISO_SKY_ROWS,
    ISO_STEP_X,
    ISO_STEP_Y,
    ISO_Z_CHARS_PER_M,
    SCREEN_H,
    SCREEN_W,
)


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

    def _raw_screen(self, wx: float, wy: float, z_m: float = 0.0) -> tuple[int, int]:
        sx = int((wx - wy) * self.step_x)
        sy = int((wx + wy) * self.step_y - z_m * ISO_Z_CHARS_PER_M)
        return sx, sy

    def world_to_screen(
        self,
        wx: float,
        wy: float,
        z_m: float = 0.0,
        *,
        focus_wx: float | None = None,
        focus_wy: float | None = None,
    ) -> tuple[int, int]:
        sx, sy = self._raw_screen(wx, wy, z_m)
        if focus_wx is not None and focus_wy is not None:
            fx, fy = self._raw_screen(focus_wx, focus_wy, 0.0)
            sx = self.origin_x + sx - fx
            sy = self.origin_y + sy - fy
        else:
            sx = self.origin_x + sx
            sy = self.origin_y + sy
        return sx, sy

    def screen_to_world(
        self,
        gx: int,
        gy: int,
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> tuple[int, int] | None:
        """Pick nearest tile anchor at char cell (gx, gy) with camera focus."""
        best: tuple[int, int] | None = None
        best_d2 = 10**9
        margin = 4
        wx_lo, wx_hi, wy_lo, wy_hi = self.world_bounds_for_focus(
            focus_wx, focus_wy, margin=margin
        )
        for wx in range(wx_lo, wx_hi + 1):
            for wy in range(wy_lo, wy_hi + 1):
                ax, ay = self.world_to_screen(wx, wy, focus_wx=focus_wx, focus_wy=focus_wy)
                d2 = (gx - ax) ** 2 + (gy - ay) ** 2
                if d2 < best_d2:
                    best_d2 = d2
                    best = (wx, wy)
        if best_d2 > 36:
            return None
        return best

    def world_bounds_for_focus(
        self,
        focus_wx: int,
        focus_wy: int,
        *,
        margin: int = 6,
    ) -> tuple[int, int, int, int]:
        """World AABB that may project into the screen (char cells)."""
        fx_iso, fy_iso = self._raw_screen(focus_wx, focus_wy, 0.0)
        corners = (
            (0, ISO_SKY_ROWS),
            (SCREEN_W - 1, ISO_SKY_ROWS),
            (0, SCREEN_H - 1),
            (SCREEN_W - 1, SCREEN_H - 1),
        )
        wxs: list[int] = []
        wys: list[int] = []
        for gx, gy in corners:
            wx, wy = self._char_to_world(gx, gy, fx_iso, fy_iso)
            wxs.append(wx)
            wys.append(wy)
        return (
            min(wxs) - margin,
            max(wxs) + margin,
            min(wys) - margin,
            max(wys) + margin,
        )

    def _char_to_world(
        self, gx: int, gy: int, fx_iso: int, fy_iso: int, z_m: float = 0.0
    ) -> tuple[int, int]:
        rel_x = gx - self.origin_x + fx_iso
        rel_y = gy - self.origin_y + fy_iso + int(z_m * ISO_Z_CHARS_PER_M)
        half = max(1, self.step_x)
        wx_minus_wy = rel_x / half
        wx_plus_wy = rel_y / max(1, self.step_y)
        wx = int(round((wx_minus_wy + wx_plus_wy) / 2))
        wy = int(round((wx_plus_wy - wx_minus_wy) / 2))
        return wx, wy

    def view_focus(self, wx0: int, wy0: int, view_w: int, view_h: int) -> tuple[int, int]:
        return wx0 + view_w // 2, wy0 + view_h // 2

    def footprint_char_cells(self, anchor_cx: int, anchor_cy: int) -> list[tuple[int, int]]:
        """Char cells inside the 2:1 iso tile diamond."""
        from src.render.iso_footprint import iso_footprint_cells

        return iso_footprint_cells(
            anchor_cx, anchor_cy, step_x=self.step_x, step_y=self.step_y
        )

    @staticmethod
    def screen_delta_to_world(screen_dx: int, screen_dy: int) -> tuple[int, int] | None:
        """Map screen-char direction to world tile step (2:1 isometric)."""
        table: dict[tuple[int, int], tuple[int, int]] = {
            (0, -1): (-1, -1),
            (0, 1): (1, 1),
            (-1, 0): (-1, 1),
            (1, 0): (1, -1),
        }
        return table.get((screen_dx, screen_dy))
