"""Fixed bottom status strip."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM, MAP_ORIGIN_Y, MAP_VIEW_H, SCREEN_H, STATUS_STRIP_H
from src.render.screen_buffer import ScreenBuffer


class StatusStrip:
    def __init__(self):
        self._tooltip = ""
        self._tooltip_hint = True
        self.layer = "surface"
        self.turn = 0

    def set_tooltip(self, text: str, *, can_examine: bool = True) -> None:
        self._tooltip = text
        self._tooltip_hint = can_examine

    def set_status(self, layer: str, turn: int) -> None:
        self.layer = layer
        self.turn = turn

    @property
    def y0(self) -> int:
        return MAP_ORIGIN_Y + MAP_VIEW_H

    def draw(self, buf: ScreenBuffer) -> None:
        from src.constants import COLOR_UI_BG

        y1 = self.y0
        y2 = y1 + STATUS_STRIP_H - 1
        buf.fill_rect(0, y1, buf.width, STATUS_STRIP_H, bg=COLOR_UI_BG)
        buf.draw_text(2, y1, f"Layer:{self.layer}  Turn:{self.turn}", fg=COLOR_TEXT, bg=COLOR_UI_BG)
        hint = "ЛКМ — осмотр · drag — обзор · Tab — персонаж"
        if self._tooltip:
            tip = self._tooltip + (" · клик — осмотр" if self._tooltip_hint and self._tooltip else "")
            line = f"{tip}  |  {hint}"
        else:
            line = hint
        fg = COLOR_TEXT if self._tooltip else COLOR_TEXT_DIM
        buf.draw_text(2, y2, line[: buf.width - 4], fg=fg, bg=COLOR_UI_BG)
