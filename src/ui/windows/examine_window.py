"""Examine window with ASCII art."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, SCREEN_H, SCREEN_W
from src.i18n import t
from src.data.art_loader import load_art
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class ExamineWindow(ModalWindow):
    name = "examine"
    blocks_world_input = False
    MAX_ART_LINES = 32

    def __init__(self):
        w, h = 38, 42
        super().__init__(t("ui.examine.title"), x=(SCREEN_W - w) // 2, y=1, w=w, h=h, visible=False)
        self.art_id: str | None = None

    def show(self, art_id: str | None = None) -> None:
        if art_id is not None:
            self.art_id = art_id
        super().show()

    def close(self) -> None:
        super().close()
        self.art_id = None

    def handle_keys(self, inp) -> bool:
        if self.visible and inp.pressed_escape():
            self.close()
            return True
        return False

    def draw(self, buf: ScreenBuffer) -> None:
        if not self.visible:
            return
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                buf.set_fog(x, y, level=1, alpha=100)
        super().draw(buf)

    def draw_content(self, buf: ScreenBuffer) -> None:
        if not self.art_id:
            return
        entry = load_art(self.art_id)
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        art_lines = entry.art[: self.MAX_ART_LINES]
        text_reserve = 5
        max_art_h = max(1, ch - text_reserve - 1)
        shown = art_lines[:max_art_h]
        for i, line in enumerate(shown):
            buf.draw_text(cx + 1, cy + i, line[: cw - 2], fg=COLOR_HIGHLIGHT, bg=COLOR_UI_BG)
        ty = cy + len(shown)
        for i, line in enumerate(entry.examine_text[:4]):
            if ty + i >= cy + ch - 1:
                break
            buf.draw_text(cx + 1, ty + i, line[: cw - 2], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, t("ui.examine.close"), fg=COLOR_TEXT, bg=COLOR_UI_BG)
