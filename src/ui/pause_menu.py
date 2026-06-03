"""Pause menu overlay."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER, SCREEN_H, SCREEN_W
from src.render.screen_buffer import ScreenBuffer


class PauseMenu:
    OPTIONS = [
        "main_menu",
        "save",
        "save_quit",
        "quit",
    ]
    LABELS = {
        "main_menu": "В главное меню",
        "save": "Сохранить",
        "save_quit": "Сохранить и выйти",
        "quit": "Выйти без сохранения",
    }

    def __init__(self):
        self.open = False
        self.cursor = 0
        self.confirm_quit = False

    def toggle(self):
        self.open = not self.open
        self.confirm_quit = False
        self.cursor = 0

    def close(self):
        self.open = False
        self.confirm_quit = False

    def draw(self, buf: ScreenBuffer):
        if not self.open:
            return
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                buf.set_fog(x, y, level=1, alpha=160)
        w, h = 44, 14
        x, y = (SCREEN_W - w) // 2, (SCREEN_H - h) // 2
        title = "ПОДТВЕРЖДЕНИЕ" if self.confirm_quit else "ПАУЗА"
        buf.draw_box(x, y, w, h, title=title, fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        if self.confirm_quit:
            buf.draw_text(x + 4, y + 4, "Выйти без сохранения?", fg=COLOR_TEXT)
            buf.draw_text(x + 4, y + 6, "Enter — да   Esc — нет", fg=COLOR_TEXT)
            return
        for i, key in enumerate(self.OPTIONS):
            fg = COLOR_HIGHLIGHT if i == self.cursor else COLOR_TEXT
            buf.draw_text(x + 4, y + 3 + i, self.LABELS[key], fg=fg)
        buf.draw_text(x + 4, y + h - 2, "Esc — закрыть", fg=COLOR_TEXT)

    def handle_input(self, inp) -> str | None:
        """Return action id or None."""
        if not self.open:
            return None
        if self.confirm_quit:
            if inp.action_pressed():
                self.close()
                return "quit"
            if inp.pressed(pygame.K_ESCAPE):
                self.confirm_quit = False
            return None
        if inp.pressed(pygame.K_ESCAPE):
            self.close()
            return None
        if inp.any_pressed(pygame.K_UP, pygame.K_w):
            self.cursor = max(0, self.cursor - 1)
        if inp.any_pressed(pygame.K_DOWN, pygame.K_s):
            self.cursor = min(len(self.OPTIONS) - 1, self.cursor + 1)
        if inp.action_pressed():
            choice = self.OPTIONS[self.cursor]
            if choice == "quit":
                self.confirm_quit = True
                return None
            self.close()
            return choice
        return None
