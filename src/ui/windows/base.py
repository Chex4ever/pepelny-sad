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
        if not self.visible or gy != self.y:
            return False
        close_x = self.x + self.w - 2
        min_x = self.x + self.w - 4
        return self.x <= gx < self.x + self.w and gx not in (close_x, min_x)

    def close_button_hit(self, gx: int, gy: int) -> bool:
        return self.visible and gy == self.y and gx == self.x + self.w - 2

    def minimize_button_hit(self, gx: int, gy: int) -> bool:
        return self.visible and gy == self.y and gx == self.x + self.w - 4

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

        ty = self.y
        buf.set(self.x, ty, "┌", fg, bg)
        for ix in range(1, self.w - 1):
            if ix in (self.w - 4, self.w - 2):
                continue
            buf.set(self.x + ix, ty, "─", fg, bg)
        buf.set(self.x + self.w - 1, ty, "┐", fg, bg)

        title_slot = max(0, self.w - 7)
        buf.draw_text(self.x + 1, ty, f" {self.title[:title_slot]} ", fg=COLOR_TEXT, bg=bg)
        buf.draw_text(self.x + self.w - 4, ty, "−", fg=COLOR_TEXT, bg=bg)
        buf.draw_text(self.x + self.w - 2, ty, "×", fg=COLOR_TEXT, bg=bg)

        if draw_h > 1:
            for iy in range(1, draw_h - 1):
                buf.set(self.x, self.y + iy, "│", fg, bg)
                buf.set(self.x + self.w - 1, self.y + iy, "│", fg, bg)
            by = self.y + draw_h - 1
            for ix in range(self.w):
                ch = "└" if ix == 0 else "┘" if ix == self.w - 1 else "─"
                buf.set(self.x + ix, by, ch, fg, bg)

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
        if self.contains(gx, gy) and (
            inp.mouse_left_down()
            or inp.mouse_left_held()
            or inp.mouse_left_released()
            or inp.mouse_middle_down()
            or inp.mouse_middle_held()
            or inp.mouse_middle_released()
        ):
            return True
        return False

    def handle_keys(self, inp) -> bool:
        return False


def buf_safe_max_x(w: int, x: int) -> int:
    from src.constants import SCREEN_W

    return min(x, SCREEN_W - w)


def buf_safe_max_y(h: int, y: int) -> int:
    from src.constants import MAP_ORIGIN_Y, MAP_VIEW_H

    return min(y, MAP_ORIGIN_Y + MAP_VIEW_H - h)
