"""COGMIND-style log panel."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM
from src.render.screen_buffer import ScreenBuffer


class LogPanel:
    def __init__(self, width: int = 38, height: int = 12):
        self.lines: list[str] = []
        self.width = width
        self.height = height

    def add(self, msg: str):
        self.lines.append(msg)
        if len(self.lines) > 100:
            self.lines = self.lines[-100:]

    def draw(self, buf: ScreenBuffer, x: int, y: int):
        buf.draw_box(x, y, self.width, self.height, "LOG")
        visible = self.lines[-(self.height - 2) :]
        for i, line in enumerate(visible):
            fg = COLOR_TEXT if i == len(visible) - 1 else COLOR_TEXT_DIM
            buf.draw_text(x + 1, y + 1 + i, line[: self.width - 2], fg=fg)
