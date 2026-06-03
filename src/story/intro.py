"""Skippable intro after new game — Undertale-style typewriter."""
from __future__ import annotations

import pygame

from src.constants import COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER, SCREEN_H
from src.render.screen_buffer import ScreenBuffer
from src.story.voices import intro_voice
from src.ui.typewriter_dialogue import TypewriterDialogue

INTRO_LINES = [
    "Элион шёл по Степям Пепла.",
    "Он искал последнюю искру Лиры —",
    "ту, что когда-то согревала сад.",
    "Ветер шептал имена. Пепел помнил.",
    "Слушай. Смотри. Не спеши сражаться.",
]


class IntroScene:
    def __init__(self):
        self.writer = TypewriterDialogue()
        self.done = False

    @property
    def line_idx(self) -> int:
        return self.writer.line_idx

    def reset(self):
        self.done = False
        self.writer.open(INTRO_LINES, intro_voice())

    def update(self, dt_ms: int, audio=None):
        if not self.done:
            self.writer.update(dt_ms, audio)

    def handle_input(self, inp) -> bool:
        if self.done:
            return True
        if inp.held(pygame.K_SPACE):
            self.writer.skip_all()
            self.done = True
            return True
        if inp.confirm_pressed() or inp.any_key_pressed():
            if self.writer.advance():
                self.done = True
                return True
        return False

    def draw(self, buf: ScreenBuffer):
        buf.clear(bg=(12, 14, 18))
        buf.draw_box(15, 12, 70, 14, title=" ПЕПЕЛЬНЫЙ САД ", fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        for i in range(self.writer.line_idx):
            buf.draw_text(20, 15 + i, INTRO_LINES[i][:66], fg=COLOR_TEXT)
        if self.writer.active and not self.done:
            from src.constants import COLOR_HIGHLIGHT

            fg = COLOR_HIGHLIGHT if not self.writer.line_complete() else COLOR_TEXT
            buf.draw_text(20, 15 + self.writer.line_idx, self.writer.visible_text()[:66], fg=fg)
        buf.draw_text(20, SCREEN_H - 3, "Enter / клик — далее · Space — пропустить", fg=COLOR_TEXT)
