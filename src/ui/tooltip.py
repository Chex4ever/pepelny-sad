"""Bottom-right hover tooltip."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM
from src.render.screen_buffer import ScreenBuffer


class Tooltip:
    def __init__(self):
        self.text = ""
        self.hint = ""

    def set(self, name: str, can_examine: bool = True):
        self.text = name
        self.hint = " · клик — осмотр" if can_examine and name else ""

    def clear(self):
        self.text = ""
        self.hint = ""

    def draw(self, buf: ScreenBuffer):
        if not self.text:
            return
        line = (self.text + self.hint)[: buf.width - 4]
        x = max(0, buf.width - len(line) - 2)
        y = buf.height - 1
        buf.draw_text(x, y, line, fg=COLOR_TEXT_DIM if not self.hint else COLOR_TEXT)
