"""Fixed bottom status strip — tooltip only; hints live in F1."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM, MAP_ORIGIN_Y, MAP_VIEW_H, STATUS_STRIP_H
from src.i18n import t
from src.render.screen_buffer import ScreenBuffer


class StatusStrip:
    def __init__(self):
        self._tooltip = ""
        self._layer = "surface"
        self._turn = 0
        self._pan_x = 0
        self._pan_y = 0

    def set_tooltip(self, text: str, *, can_examine: bool = True) -> None:
        self._tooltip = text

    def set_status(self, layer: str, turn: int, *, pan_x: int = 0, pan_y: int = 0) -> None:
        self._layer = layer
        self._turn = turn
        self._pan_x = pan_x
        self._pan_y = pan_y

    @property
    def y0(self) -> int:
        return MAP_ORIGIN_Y + MAP_VIEW_H

    def draw(self, buf: ScreenBuffer) -> None:
        from src.constants import COLOR_UI_BG

        y = self.y0
        buf.fill_rect(0, y, buf.width, STATUS_STRIP_H, bg=COLOR_UI_BG)
        parts: list[str] = []
        if self._tooltip:
            parts.append(self._tooltip[:40])
        if self._pan_x or self._pan_y:
            parts.append(t("ui.status.camera_pan", x=self._pan_x, y=self._pan_y))
        if parts:
            line = " · ".join(parts)
            buf.draw_text(2, y, line[: buf.width - 4], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        else:
            buf.draw_text(2, y, "─" * min(20, buf.width - 4), fg=COLOR_TEXT_DIM, bg=COLOR_UI_BG)
