"""Window registry and z-order."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.input import InputState
    from src.render.screen_buffer import ScreenBuffer
    from src.ui.windows.base import ModalWindow


class WindowManager:
    def __init__(self):
        self._windows: list[ModalWindow] = []

    def register(self, window: ModalWindow) -> None:
        self._windows.append(window)

    def get(self, name: str) -> ModalWindow | None:
        for w in self._windows:
            if getattr(w, "name", None) == name:
                return w
        return None

    def focus(self, window: ModalWindow) -> None:
        if window in self._windows:
            self._windows.remove(window)
            self._windows.append(window)
        for w in self._windows:
            w.focused = w is window

    def any_blocking_world(self) -> bool:
        return any(w.visible and w.blocks_world_input for w in self._windows)

    def topmost_blocking(self) -> ModalWindow | None:
        for w in reversed(self._windows):
            if w.visible and w.blocks_world_input:
                return w
        return None

    def close_topmost(self) -> bool:
        for w in reversed(self._windows):
            if w.visible and w.blocks_world_input:
                w.close()
                return True
        return False

    def examine_open(self) -> bool:
        ex = self.get("examine")
        return ex is not None and ex.visible

    def close_examine(self) -> None:
        ex = self.get("examine")
        if ex:
            ex.close()

    def handle_input(self, inp: InputState) -> bool:
        gx, gy = inp.mouse_grid()
        if inp.mouse_left_down():
            for w in reversed(self._windows):
                if w.visible and w.contains(gx, gy):
                    self.focus(w)
                    break
        for w in reversed(self._windows):
            if not w.visible:
                continue
            if w.handle_input(inp, gx, gy):
                return True
            if w.handle_keys(inp):
                return True
        return False

    def draw(self, buf: ScreenBuffer) -> None:
        for w in self._windows:
            if w.visible:
                w.draw(buf)
