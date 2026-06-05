"""Full-screen fade transitions between scenes."""
from __future__ import annotations


class TransitionManager:
    FADE_OUT_MS = 250
    FADE_IN_MS = 250

    def __init__(self):
        self.active = False
        self.mode = "out"
        self.elapsed_ms = 0
        self.pending_scene: str | None = None
        self.on_midpoint = None
        self._auto_fade_in = True

    def start(self, mode: str = "out", pending_scene: str | None = None, callback=None, *, auto_fade_in: bool = True):
        self.active = True
        self.mode = mode
        self.elapsed_ms = 0
        self.pending_scene = pending_scene
        self.on_midpoint = callback
        self._auto_fade_in = auto_fade_in

    def start_fade_out(self, callback) -> None:
        self.start("out", callback=callback, auto_fade_in=False)

    def start_fade_in(self) -> None:
        self.start("in", auto_fade_in=False)

    def update(self, dt_ms: int) -> str | None:
        if not self.active:
            return None
        self.elapsed_ms += dt_ms
        duration = self.FADE_OUT_MS if self.mode == "out" else self.FADE_IN_MS
        if self.elapsed_ms < duration:
            return None
        if self.mode == "out":
            scene = self.pending_scene
            if self.on_midpoint:
                self.on_midpoint()
            if self._auto_fade_in:
                self.mode = "in"
                self.elapsed_ms = 0
                self.pending_scene = None
            else:
                self.active = False
                self.elapsed_ms = 0
                self.pending_scene = None
            return scene
        self.active = False
        self.elapsed_ms = 0
        return None

    def alpha(self) -> int:
        if not self.active:
            return 0
        duration = self.FADE_OUT_MS if self.mode == "out" else self.FADE_IN_MS
        t = min(1.0, self.elapsed_ms / max(1, duration))
        if self.mode == "in":
            t = 1.0 - t
        return int(255 * t)

    def blocks_input(self) -> bool:
        return self.active and self.mode == "out"

    def blocks_scene_logic(self) -> bool:
        """Block scene update/input during any active fade (e.g. intro typewriter)."""
        return self.active
