"""Enemy portrait in battle."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT
from src.data.art_loader import load_art
from src.render.screen_buffer import ScreenBuffer


def draw_enemy_portrait(buf: ScreenBuffer, art_id: str, x: int = 4, y: int = 2):
    entry = load_art(art_id)
    for i, line in enumerate(entry.art[:6]):
        buf.draw_text(x, y + i, line, fg=COLOR_HIGHLIGHT)
    for i, line in enumerate(entry.examine_text[:2]):
        buf.draw_text(x, y + 8 + i, line[:40], fg=COLOR_TEXT)
