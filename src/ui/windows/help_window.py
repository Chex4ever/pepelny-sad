"""F1 help modal window."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_UI_BG
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow

HELP_LINES = [
    "WASD — ход",
    "E — действие / сбор",
    "Tab — персонаж",
    "ЛКМ — осмотр · drag — обзор",
    "O — осмотр под курсором / себя",
    "F5 — сохранить · F9 — загрузка",
    "F1 — эта справка · F4 — debug",
    "Esc — пауза · закрыть окно",
    "Бой: стрелки + Enter, dodge WASD",
    "Fight QTE: Space",
    "Окна: drag заголовок, − свернуть, × закрыть",
    "Осмотр не блокирует движение",
]


class HelpWindow(ModalWindow):
    name = "help"
    blocks_world_input = False

    def __init__(self):
        super().__init__("СПРАВКА F1", x=58, y=2, w=40, h=17, visible=False)

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.show()

    def handle_keys(self, inp) -> bool:
        if self.visible and (inp.pressed_f1() or inp.pressed_escape()):
            self.close()
            return True
        return False

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        for i, line in enumerate(HELP_LINES):
            if cy + i >= cy + ch - 1:
                break
            buf.draw_text(cx + 1, cy + i, line[: cw - 2], fg=COLOR_TEXT, bg=COLOR_UI_BG)
        buf.draw_text(cx + 1, cy + ch - 1, "F1/Esc — закрыть", fg=COLOR_TEXT, bg=COLOR_UI_BG)
