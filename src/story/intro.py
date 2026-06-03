"""Skippable intro after new game."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER, SCREEN_H
from src.render.screen_buffer import ScreenBuffer

INTRO_LINES = [
    "Элион шёл по Степям Пепла.",
    "Он искал последнюю искру Лиры —",
    "ту, что когда-то согревала сад.",
    "Ветер шептал имена. Пепел помнил.",
    "Слушай. Смотри. Не спеши сражаться.",
]


class IntroScene:
    def __init__(self):
        self.line_idx = 0
        self.done = False

    def reset(self):
        self.line_idx = 0
        self.done = False

    def handle_input(self, inp) -> bool:
        if self.done:
            return True
        # Plan: skip on any key, click, or holding Space.
        if inp.held(pygame.K_SPACE):
            self.done = True
            return True
        if inp.confirm_pressed() or inp.any_key_pressed():
            self.line_idx += 1
            if self.line_idx >= len(INTRO_LINES):
                self.done = True
                return True
        return False

    def draw(self, buf: ScreenBuffer):
        buf.clear(bg=(12, 14, 18))
        buf.draw_box(15, 12, 70, 14, title=" ПЕПЕЛЬНЫЙ САД ", fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        for i in range(min(self.line_idx + 1, len(INTRO_LINES))):
            fg = COLOR_HIGHLIGHT if i == self.line_idx else COLOR_TEXT
            buf.draw_text(20, 15 + i, INTRO_LINES[i][:66], fg=fg)
        buf.draw_text(20, SCREEN_H - 3, "Enter / клик / Esc — далее (пропустить)", fg=COLOR_TEXT)
