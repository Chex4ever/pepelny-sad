"""Double-buffered ASCII screen."""
from __future__ import annotations


class ScreenBuffer:
    __slots__ = ("width", "height", "chars", "fg", "bg", "light")

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        n = width * height
        self.chars = [" "] * n
        self.fg = [(200, 200, 200)] * n
        self.bg = [(10, 10, 20)] * n
        self.light = [1.0] * n

    def clear(self, ch=" ", fg=(180, 190, 200), bg=(8, 8, 18), light=1.0):
        n = self.width * self.height
        self.chars = [ch] * n
        self.fg = [fg] * n
        self.bg = [bg] * n
        self.light = [light] * n

    def _idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set(self, x: int, y: int, ch: str, fg=(200, 200, 200), bg=(10, 10, 20), light: float = 1.0):
        if not self.in_bounds(x, y):
            return
        i = self._idx(x, y)
        self.chars[i] = ch
        self.fg[i] = fg
        self.bg[i] = bg
        self.light[i] = light

    def get(self, x: int, y: int) -> str:
        if not self.in_bounds(x, y):
            return " "
        return self.chars[self._idx(x, y)]

    def draw_text(self, x: int, y: int, text: str, fg=(200, 200, 200), bg=None, light: float = 1.0):
        for i, ch in enumerate(text):
            px = x + i
            if px >= self.width:
                break
            if bg is None and self.in_bounds(px, y):
                bg = self.bg[self._idx(px, y)]
            self.set(px, y, ch, fg=fg, bg=bg if bg else (10, 10, 20), light=light)

    def draw_box(self, x: int, y: int, w: int, h: int, title: str = "", fg=(100, 140, 180), bg=(16, 16, 28)):
        if w < 2 or h < 2:
            return
        corners = ["┌", "┐", "└", "┘"]
        for ix in range(w):
            top = corners[0] if ix == 0 else corners[1] if ix == w - 1 else "─"
            bot = corners[2] if ix == 0 else corners[3] if ix == w - 1 else "─"
            self.set(x + ix, y, top, fg, bg)
            self.set(x + ix, y + h - 1, bot, fg, bg)
        for iy in range(1, h - 1):
            self.set(x, y + iy, "│", fg, bg)
            self.set(x + w - 1, y + iy, "│", fg, bg)
        if title:
            self.draw_text(x + 2, y, f" {title[: w - 4]} ", fg=(200, 210, 220), bg=bg)

    def blit(self, src: "ScreenBuffer", dx: int, dy: int, sx=0, sy=0, sw=None, sh=None):
        sw = sw or src.width
        sh = sh or src.height
        for y in range(sh):
            for x in range(sw):
                tx, ty = dx + x, dy + y
                if not self.in_bounds(tx, ty):
                    continue
                si = y * src.width + x
                ti = self._idx(tx, ty)
                self.chars[ti] = src.chars[si]
                self.fg[ti] = src.fg[si]
                self.bg[ti] = src.bg[si]
                self.light[ti] = src.light[si]
