"""Pause menu modal window."""
from __future__ import annotations

from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT, COLOR_UI_BG, SCREEN_H, SCREEN_W
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.base import ModalWindow


class PauseWindow(ModalWindow):
    name = "pause"
    OPTIONS = ["main_menu", "save", "save_quit", "quit"]
    LABELS = {
        "main_menu": "В главное меню",
        "save": "Сохранить",
        "save_quit": "Сохранить и выйти",
        "quit": "Выйти без сохранения",
    }

    def __init__(self):
        w, h = 44, 14
        super().__init__("ПАУЗА", x=(SCREEN_W - w) // 2, y=(SCREEN_H - h) // 2, w=w, h=h, visible=False)
        self.cursor = 0
        self.confirm_quit = False

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.show()
            self.confirm_quit = False
            self.cursor = 0

    def close(self) -> None:
        super().close()
        self.confirm_quit = False

    def draw(self, buf: ScreenBuffer) -> None:
        if not self.visible:
            return
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                buf.set_fog(x, y, level=1, alpha=160)
        self.title = "ПОДТВЕРЖДЕНИЕ" if self.confirm_quit else "ПАУЗА"
        super().draw(buf)

    def draw_content(self, buf: ScreenBuffer) -> None:
        cx, cy, cw, ch = self.content_rect()
        buf.fill_rect(cx, cy, cw, ch, bg=COLOR_UI_BG)
        if self.confirm_quit:
            buf.draw_text(cx + 3, cy + 2, "Выйти без сохранения?", fg=COLOR_TEXT, bg=COLOR_UI_BG)
            buf.draw_text(cx + 3, cy + 4, "Enter — да   Esc — нет", fg=COLOR_TEXT, bg=COLOR_UI_BG)
            return
        for i, key in enumerate(self.OPTIONS):
            fg = COLOR_HIGHLIGHT if i == self.cursor else COLOR_TEXT
            buf.draw_text(cx + 3, cy + 1 + i, self.LABELS[key], fg=fg, bg=COLOR_UI_BG)
        buf.draw_text(cx + 3, cy + ch - 1, "Esc — закрыть", fg=COLOR_TEXT, bg=COLOR_UI_BG)

    def handle_input(self, inp) -> str | None:
        return self.handle_menu_input(inp)

    def handle_menu_input(self, inp) -> str | None:
        if not self.visible:
            return None
        if self.confirm_quit:
            if inp.action_pressed():
                self.close()
                return "quit"
            if inp.pressed_escape():
                self.confirm_quit = False
            return None
        if inp.pressed_escape():
            self.close()
            return None
        if inp.nav_up_pressed():
            self.cursor = max(0, self.cursor - 1)
        if inp.nav_down_pressed():
            self.cursor = min(len(self.OPTIONS) - 1, self.cursor + 1)
        if inp.action_pressed():
            choice = self.OPTIONS[self.cursor]
            if choice == "quit":
                self.confirm_quit = True
                return None
            self.close()
            return choice
        return None
