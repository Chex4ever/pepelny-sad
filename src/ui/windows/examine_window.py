"""Examine window with ASCII art."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG
from src.data.art_loader import load_art
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class ExamineWindow(ModalWindow):
    name = "examine"
    blocks_world_input = False

    def __init__(self):
        super().__init__("ОСМОТР", x=62, y=4, w=36, h=22, visible=False)
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

    def draw_content(self, buf: ScreenBuffer) -> None:
        if not self.art_id:
            return
        entry = load_art(self.art_id)
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        for i, line in enumerate(entry.art[:10]):
            buf.draw_text(cx + 1, cy + i, line[: cw - 2], fg=COLOR_HIGHLIGHT, bg=COLOR_UI_BG)
        ty = cy + len(entry.art[:10]) + 1
        for i, line in enumerate(entry.examine_text[:4]):
            buf.draw_text(cx + 1, ty + i, line[: cw - 2], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, "Esc — закрыть", fg=COLOR_TEXT, bg=COLOR_UI_BG)
