"""Floating log window."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_TEXT_DIM, COLOR_UI_BG
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class LogWindow(ModalWindow):
    name = "log"
    blocks_world_input = False

    def __init__(self):
        super().__init__("LOG", x=72, y=1, w=26, h=14, visible=False)
        self.lines: list[str] = []

    def add(self, msg: str) -> None:
        self.lines.append(msg)
        if len(self.lines) > 100:
            self.lines = self.lines[-100:]

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        visible = self.lines[-(ch - 1) :]
        for i, line in enumerate(visible):
            fg = COLOR_TEXT if i == len(visible) - 1 else COLOR_TEXT_DIM
            buf.draw_text(cx, cy + i, line[: cw], fg=fg, bg=COLOR_UI_BG)
