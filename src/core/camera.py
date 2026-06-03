"""Viewport camera with optional pan offset."""
from __future__ import annotations


class Camera:
    def __init__(self, view_w: int, view_h: int, pan_limit: int = 15):
        self.view_w = view_w
        self.view_h = view_h
        self.pan_limit = pan_limit
        self._center_x = 0
        self._center_y = 0
        self.pan_x = 0
        self.pan_y = 0

    def center_on(self, world_x: int, world_y: int) -> None:
        self._center_x = world_x
        self._center_y = world_y

    def view_origin(self) -> tuple[int, int]:
        wx0 = self._center_x - self.view_w // 2 + self.pan_x
        wy0 = self._center_y - self.view_h // 2 + self.pan_y
        return wx0, wy0

    def pan_by(self, dx: int, dy: int) -> None:
        self.pan_x = max(-self.pan_limit, min(self.pan_limit, self.pan_x + dx))
        self.pan_y = max(-self.pan_limit, min(self.pan_limit, self.pan_y + dy))

    def reset_pan(self) -> None:
        self.pan_x = 0
        self.pan_y = 0

    def screen_to_world(self, screen_x: int, screen_y: int, origin_y: int = 0) -> tuple[int, int]:
        wx0, wy0 = self.view_origin()
        return wx0 + screen_x, wy0 + (screen_y - origin_y)
