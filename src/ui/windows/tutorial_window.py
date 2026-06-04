"""Non-blocking tutorial hint panel."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, SCREEN_W
from src.i18n import t
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class TutorialWindow(ModalWindow):
    name = "tutorial"
    blocks_world_input = False

    def __init__(self):
        w = min(72, SCREEN_W - 4)
        super().__init__(t("ui.tutorial.title"), x=(SCREEN_W - w) // 2, y=38, w=w, h=6, visible=False)
        self._text = ""

    def set_text(self, text: str) -> None:
        self._text = text
        if text:
            self.show()
        else:
            self.close()

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        if self._text:
            buf.draw_text(cx + 1, cy, self._text[: cw - 2], fg=COLOR_HIGHLIGHT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, t("ui.tutorial.footer"), fg=COLOR_TEXT, bg=COLOR_UI_BG)
