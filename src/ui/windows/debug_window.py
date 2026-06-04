"""F4 debug overlay (Minecraft-style stats)."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_UI_BG
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class DebugWindow(ModalWindow):
    name = "debug"
    blocks_world_input = False

    def __init__(self):
        super().__init__("DEBUG F4", x=1, y=1, w=52, h=24, visible=False)
        self._lines: list[str] = []

    def set_lines(self, lines: list[str]) -> None:
        self._lines = lines

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.show()

    def handle_keys(self, inp) -> bool:
        return False

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        for i, line in enumerate(self._lines):
            if cy + i >= cy + ch - 1:
                break
            buf.draw_text(cx + 1, cy + i, line[: cw - 2], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, "F4/Esc — закрыть", fg=COLOR_TEXT, bg=COLOR_UI_BG)
