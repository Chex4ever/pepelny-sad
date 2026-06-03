"""Fixed bottom status strip — tooltip only; hints live in F1."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM, MAP_ORIGIN_Y, MAP_VIEW_H, STATUS_STRIP_H
from src.render.screen_buffer import ScreenBuffer


class StatusStrip:
    def __init__(self):
        self._tooltip = ""

    def set_tooltip(self, text: str, *, can_examine: bool = True) -> None:
        self._tooltip = text

    def set_status(self, layer: str, turn: int) -> None:
        """Kept for callers; stats moved to F4 debug overlay."""
        pass

    @property
    def y0(self) -> int:
        return MAP_ORIGIN_Y + MAP_VIEW_H

    def draw(self, buf: ScreenBuffer) -> None:
        from src.constants import COLOR_UI_BG

        y = self.y0
        buf.fill_rect(0, y, buf.width, STATUS_STRIP_H, bg=COLOR_UI_BG)
        if self._tooltip:
            buf.draw_text(2, y, self._tooltip[: buf.width - 4], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        else:
            buf.draw_text(2, y, "─" * min(20, buf.width - 4), fg=COLOR_TEXT_DIM, bg=COLOR_UI_BG)
