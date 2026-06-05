"""Shared UI font for GPU glyph atlas and CPU renderer."""
from __future__ import annotations

import pygame

from src.constants import CELL_H

_FONT: pygame.font.Font | None = None


def ui_font() -> pygame.font.Font:
    global _FONT
    if _FONT is not None:
        try:
            _FONT.render(" ", True, (255, 255, 255))
            return _FONT
        except pygame.error:
            _FONT = None
    if not pygame.font.get_init():
        pygame.font.init()
    _FONT = pygame.font.SysFont("consolas,courier,cascadiamono", CELL_H)
    if _FONT is None:
        _FONT = pygame.font.Font(None, CELL_H + 4)
    return _FONT


def static_ui_characters() -> list[str]:
    """ASCII + Cyrillic + common punctuation for menus."""
    chars: list[str] = [chr(c) for c in range(32, 127)]
    chars.extend(chr(c) for c in range(0x0410, 0x0452))  # А-я, ё
    for ch in "Ё«»—–…°×−":
        if ch not in chars:
            chars.append(ch)
    return chars
