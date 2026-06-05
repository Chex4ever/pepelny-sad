"""Viewport camera with optional pan offset and smooth follow."""
from __future__ import annotations


class Camera:
    def __init__(self, view_w: int, view_h: int, pan_limit: int | None = None):
        self.view_w = view_w
        self.view_h = view_h
        self.pan_limit = pan_limit if pan_limit is not None else max(view_w, view_h) // 3
        self._center_x = 0.0
        self._center_y = 0.0
        self.pan_x = 0
        self.pan_y = 0

    def center_on(self, world_x: float, world_y: float) -> None:
        self._center_x = float(world_x)
        self._center_y = float(world_y)

    def follow_smooth(self, world_x: float, world_y: float, dt_ms: int, *, rate: float = 14.0) -> None:
        t = min(1.0, rate * (dt_ms / 1000.0))
        self._center_x += (float(world_x) - self._center_x) * t
        self._center_y += (float(world_y) - self._center_y) * t

    def view_origin(self) -> tuple[int, int]:
        wx0 = int(self._center_x) - self.view_w // 2 + self.pan_x
        wy0 = int(self._center_y) - self.view_h // 2 + self.pan_y
        return wx0, wy0

    def focus_float(self) -> tuple[float, float]:
        return self._center_x + self.pan_x, self._center_y + self.pan_y

    def set_pan(self, px: int, py: int) -> None:
        self.pan_x = max(-self.pan_limit, min(self.pan_limit, px))
        self.pan_y = max(-self.pan_limit, min(self.pan_limit, py))

    def pan_by(self, dx: int, dy: int) -> None:
        self.set_pan(self.pan_x + dx, self.pan_y + dy)

    def pan_from_drag(
        self,
        total_dx_px: int,
        total_dy_px: int,
        cell_w: int,
        cell_h: int,
        base_pan_x: int,
        base_pan_y: int,
        *,
        iso: bool = False,
    ) -> None:
        if iso:
            from src.constants import ISO_STEP_X, ISO_STEP_Y

            step_x_px = max(1, ISO_STEP_X * cell_w)
            step_y_px = max(1, ISO_STEP_Y * cell_h)
            px = base_pan_x - round(total_dx_px / step_x_px)
            py = base_pan_y - round(total_dy_px / step_y_px)
        else:
            px = base_pan_x - round(total_dx_px / cell_w)
            py = base_pan_y - round(total_dy_px / cell_h)
        self.set_pan(px, py)

    def is_panned(self) -> bool:
        return self.pan_x != 0 or self.pan_y != 0

    def is_at_limit(self) -> bool:
        return abs(self.pan_x) >= self.pan_limit or abs(self.pan_y) >= self.pan_limit

    def reset_pan(self) -> None:
        self.pan_x = 0
        self.pan_y = 0

    def screen_to_world(self, screen_x: int, screen_y: int, origin_y: int = 0) -> tuple[int, int]:
        wx0, wy0 = self.view_origin()
        return wx0 + screen_x, wy0 + (screen_y - origin_y)
