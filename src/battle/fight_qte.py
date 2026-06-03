"""Fight timing QTE."""
from __future__ import annotations


class FightQTE:
    def __init__(self, fight_mode: str = "blade"):
        self.fight_mode = fight_mode
        self.active = False
        self.cursor = 0.0
        self.speed = 0.025
        self.window_start = 0.42 if fight_mode == "blade" else 0.28
        self.window_end = 0.52 if fight_mode == "blade" else 0.62
        self.result = None

    def start(self):
        self.active = True
        self.cursor = 0.0
        self.result = None

    def update(self):
        if not self.active:
            return
        self.cursor += self.speed
        if self.cursor > 1.0:
            self.cursor = 0.0

    def try_hit(self) -> bool:
        if not self.active:
            return False
        ok = self.window_start <= self.cursor <= self.window_end
        self.active = False
        self.result = ok
        return ok
