"""F1 help modal window."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_UI_BG, SCREEN_H, SCREEN_W
from src.i18n import t, t_list
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class HelpWindow(ModalWindow):
    name = "help"
    blocks_world_input = False

    def __init__(self):
        super().__init__(t("ui.help.title"), x=58, y=2, w=40, h=17, visible=False)

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.show()

    def handle_keys(self, inp) -> bool:
        return False

    def draw(self, buf: ScreenBuffer) -> None:
        if not self.visible:
            return
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                buf.set_fog(x, y, level=1, alpha=120)
        super().draw(buf)

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        for i, line in enumerate(t_list("ui.help.lines")):
            if cy + i >= cy + ch - 1:
                break
            buf.draw_text(cx + 1, cy + i, line[: cw - 2], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, t("ui.help.close"), fg=COLOR_TEXT, bg=COLOR_UI_BG)
