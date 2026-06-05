"""Loading screen while world / new game is prepared."""
from __future__ import annotations

import math

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_UI_BG, SCREEN_H, SCREEN_W
from src.i18n import t


def draw_loading(buf, message: str, *, elapsed_ms: int = 0, progress: float | None = None) -> None:
    buf.clear(bg=(10, 12, 20))
    title = t("loading.title")
    buf.draw_box(20, 14, 60, 12, title=title, fg=(80, 100, 120), bg=COLOR_UI_BG)
    buf.draw_text(24, 17, message[:56], fg=COLOR_HIGHLIGHT)
    if progress is not None:
        bar_w = 50
        filled = int(bar_w * max(0.0, min(1.0, progress)))
        y = 22
        for x in range(bar_w):
            ch = "█" if x < filled else "░"
            fg = COLOR_HIGHLIGHT if x < filled else COLOR_TEXT_DIM
            buf.draw_text(24 + x, y, ch, fg=fg)
    pulse = 0.5 + 0.5 * math.sin(elapsed_ms / 200.0)
    dots = "." * (1 + (elapsed_ms // 400) % 3)
    buf.draw_text(24, 24, dots.ljust(3), fg=COLOR_TEXT_DIM, light=pulse)
    buf.draw_text(22, SCREEN_H - 4, t("loading.wait"), fg=COLOR_TEXT_DIM)
