"""Examine overlay with ASCII art."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER
from src.data.art_loader import load_art
from src.render.screen_buffer import ScreenBuffer


class ExaminePanel:
    def __init__(self):
        self.art_id: str | None = None
        self.open = False

    def show(self, art_id: str):
        self.art_id = art_id
        self.open = True

    def close(self):
        self.open = False
        self.art_id = None

    def draw(self, buf: ScreenBuffer):
        if not self.open or not self.art_id:
            return
        entry = load_art(self.art_id)
        w, h = 36, 22
        x = buf.width - w - 2
        y = 4
        buf.draw_box(x, y, w, h, "ОСМОТР", fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        for i, line in enumerate(entry.art[:10]):
            buf.draw_text(x + 2, y + 2 + i, line[: w - 4], fg=COLOR_HIGHLIGHT)
        ty = y + 2 + len(entry.art[:10]) + 1
        for i, line in enumerate(entry.examine_text[:4]):
            buf.draw_text(x + 2, ty + i, line[: w - 4], fg=COLOR_TEXT)
        buf.draw_text(x + 2, y + h - 2, "Esc — закрыть", fg=COLOR_TEXT)
