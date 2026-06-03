"""Undertale-style letter-by-letter dialogue with voice blips."""
from __future__ import annotations

import pygame

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER
from src.render.screen_buffer import ScreenBuffer

# ms per visible character
CHAR_MS = 36
PUNCT_PAUSE_MS = {
    ".": 260,
    "!": 260,
    "?": 260,
    "…": 320,
    ",": 110,
    "—": 140,
    ":": 120,
    ";": 120,
}


class TypewriterDialogue:
    """One line at a time; blip on each non-space character."""

    def __init__(self):
        self.lines: list[str] = []
        self.line_idx = 0
        self.voice = "default"
        self.active = False
        self._char_idx = 0
        self._timer_ms = 0.0
        self._pause_ms = 0.0
        self._audio = None

    def open(self, lines: list[str], voice: str):
        self.lines = [ln for ln in lines if ln]
        self.line_idx = 0
        self.voice = voice or "default"
        self.active = bool(self.lines)
        self._reset_line()

    def close(self):
        self.active = False
        self.lines = []

    def _reset_line(self):
        self._char_idx = 0
        self._timer_ms = 0.0
        self._pause_ms = 0.0

    def current_line(self) -> str:
        if not self.lines or self.line_idx >= len(self.lines):
            return ""
        return self.lines[self.line_idx]

    def visible_text(self) -> str:
        line = self.current_line()
        return line[: self._char_idx]

    def line_complete(self) -> bool:
        line = self.current_line()
        return not line or self._char_idx >= len(line)

    def update(self, dt_ms: int, audio=None):
        if not self.active or self.line_complete():
            return
        self._audio = audio
        if self._pause_ms > 0:
            self._pause_ms = max(0.0, self._pause_ms - dt_ms)
            return
        self._timer_ms += dt_ms
        while self._timer_ms >= CHAR_MS and not self.line_complete():
            self._timer_ms -= CHAR_MS
            line = self.current_line()
            ch = line[self._char_idx]
            self._char_idx += 1
            self._blip(ch)
            self._pause_ms = float(PUNCT_PAUSE_MS.get(ch, 0))

    def _blip(self, ch: str):
        if ch.isspace():
            return
        if self._audio and getattr(self._audio, "enabled", False):
            variant = (self._char_idx - 1) % 2
            self._audio.play_voice_blip(self.voice, variant)

    def complete_line(self):
        line = self.current_line()
        self._char_idx = len(line)

    def skip_all(self):
        self.line_idx = len(self.lines)
        self.active = False

    def advance(self) -> bool:
        """Advance dialogue. Returns True when all lines finished."""
        if not self.active:
            return True
        if not self.line_complete():
            self.complete_line()
            return False
        self.line_idx += 1
        if self.line_idx >= len(self.lines):
            self.active = False
            return True
        self._reset_line()
        return False

    def handle_advance_input(self, inp) -> bool:
        """Confirm advances line; returns True when finished."""
        if inp.confirm_pressed() or inp.any_key_pressed():
            return self.advance()
        return False

    def draw_box(
        self,
        buf: ScreenBuffer,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        title: str = "ДИАЛОГ",
        show_prev_lines: int = 0,
        prev_x: int | None = None,
        prev_y_start: int | None = None,
    ):
        if not self.active:
            return
        buf.draw_box(x, y, w, h, title=title, fg=COLOR_UI_BORDER, bg=COLOR_UI_BG)
        ty = y + 2
        if show_prev_lines and prev_x is not None and prev_y_start is not None:
            start = max(0, self.line_idx - show_prev_lines)
            for i in range(start, self.line_idx):
                buf.draw_text(prev_x, prev_y_start + (i - start), self.lines[i][: w - 4], fg=COLOR_TEXT)
        fg = COLOR_HIGHLIGHT if not self.line_complete() else COLOR_TEXT
        buf.draw_text(x + 2, ty, self.visible_text()[: w - 4], fg=fg)
