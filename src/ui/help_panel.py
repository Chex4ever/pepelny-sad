"""F1 help overlay."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER, SCREEN_H, SCREEN_W
from src.render.screen_buffer import ScreenBuffer

HELP_LINES = [
    "WASD — ход",
    "E — действие / сбор",
    "Tab — персонаж",
    "ЛКМ — осмотр",
    "O — осмотр (клавиатура)",
    "F5 — сохранить",
    "F1 — эта справка",
    "Esc — пауза",
    "Бой: стрелки + Enter, dodge WASD",
    "Fight QTE: Space",
]


class HelpPanel:
    def __init__(self):
        self.open = False

    def toggle(self):
        self.open = not self.open

    def close(self):
        self.open = False

    def draw(self, buf: ScreenBuffer):
        if not self.open:
            return
        w, h = 38, 16
        x, y = SCREEN_W - w - 2, 2
        buf.draw_box(x, y, w, h, title="СПРАВКА F1", fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        for i, line in enumerate(HELP_LINES):
            if y + 2 + i >= y + h - 1:
                break
            buf.draw_text(x + 2, y + 2 + i, line[: w - 4], fg=COLOR_TEXT)
        buf.draw_text(x + 2, y + h - 2, "F1/Esc — закрыть", fg=COLOR_TEXT)
