"""Modal window base with chrome (drag, close, minimize)."""
from __future__ import annotations

from src.constants import COLOR_TEXT, COLOR_UI_BG, COLOR_UI_BORDER
from src.render.screen_buffer import ScreenBuffer


class ModalWindow:
    blocks_world_input = True

    def __init__(
        self,
        title: str,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        visible: bool = False,
    ):
        self.title = title
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible
        self.minimized = False
        self.focused = False
        self._dragging = False
        self._drag_off = (0, 0)

    @property
    def open(self) -> bool:
        return self.visible

    @open.setter
    def open(self, value: bool) -> None:
        self.visible = value
        if not value:
            self.minimized = False

    def show(self) -> None:
        self.visible = True
        self.minimized = False

    def close(self) -> None:
        self.visible = False
        self.minimized = False
        self.focused = False

    def toggle(self) -> None:
        if self.visible:
            self.close()
        else:
            self.show()

    def content_rect(self) -> tuple[int, int, int, int]:
        if self.minimized:
            return self.x, self.y, self.w, 1
        return self.x, self.y + 1, self.w, max(1, self.h - 1)

    def title_bar_hit(self, gx: int, gy: int) -> bool:
        return self.visible and self.x <= gx < self.x + self.w and gy == self.y

    def close_button_hit(self, gx: int, gy: int) -> bool:
        return self.visible and gy == self.y and gx == self.x + self.w - 2

    def minimize_button_hit(self, gx: int, gy: int) -> bool:
        return self.visible and gy == self.y and gx == self.x + self.w - 3

    def contains(self, gx: int, gy: int) -> bool:
        if not self.visible:
            return False
        end_y = self.y + (1 if self.minimized else self.h)
        return self.x <= gx < self.x + self.w and self.y <= gy < end_y

    def draw_chrome(self, buf: ScreenBuffer) -> None:
        if not self.visible:
            return
        fg = COLOR_UI_BORDER
        bg = COLOR_UI_BG
        draw_h = 1 if self.minimized else self.h
        buf.fill_rect(self.x, self.y, self.w, draw_h, bg=bg)
        buf.draw_box(self.x, self.y, self.w, draw_h, title="", fg=fg, bg=bg)
        title_text = f" {self.title[: self.w - 8]} "
        buf.draw_text(self.x + 1, self.y, title_text, fg=COLOR_TEXT, bg=bg)
        buf.draw_text(self.x + self.w - 3, self.y, "[−]", fg=COLOR_TEXT, bg=bg)
        buf.draw_text(self.x + self.w - 2, self.y, "[×]", fg=COLOR_TEXT, bg=bg)

    def draw(self, buf: ScreenBuffer) -> None:
        self.draw_chrome(buf)
        if self.visible and not self.minimized:
            self.draw_content(buf)

    def draw_content(self, buf: ScreenBuffer) -> None:
        pass

    def handle_input(self, inp, gx: int, gy: int) -> bool:
        """Return True if input consumed."""
        if not self.visible:
            return False
        if inp.mouse_left_down():
            if self.close_button_hit(gx, gy):
                self.close()
                return True
            if self.minimize_button_hit(gx, gy):
                self.minimized = not self.minimized
                return True
            if self.title_bar_hit(gx, gy):
                self._dragging = True
                self._drag_off = (gx - self.x, gy - self.y)
                return True
        if inp.mouse_left_released():
            self._dragging = False
        if self._dragging and inp.mouse_left_held():
            ngx, ngy = inp.mouse_grid()
            self.x = max(0, buf_safe_max_x(self.w, ngx - self._drag_off[0]))
            self.y = max(0, buf_safe_max_y(self.h, ngy - self._drag_off[1]))
            return True
        return self.contains(gx, gy)

    def handle_keys(self, inp) -> bool:
        return False


def buf_safe_max_x(w: int, x: int) -> int:
    from src.constants import SCREEN_W

    return min(x, SCREEN_W - w)


def buf_safe_max_y(h: int, y: int) -> int:
    from src.constants import MAP_VIEW_H, MAP_ORIGIN_Y

    return min(y, MAP_ORIGIN_Y + MAP_VIEW_H - h)
