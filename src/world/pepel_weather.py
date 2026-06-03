"""Pepel weather cycle on surface."""
from __future__ import annotations

import random


class PepelWeather:
    def __init__(self, seed: int):
        self.rng = random.Random(seed + 777)
        self.turns_until = self.rng.randint(18, 25)
        self.active = False
        self.remaining = 0

    def on_turn(self, in_shelter: bool) -> tuple[bool, int]:
        fov_penalty = 0
        if self.active:
            self.remaining -= 1
            if self.remaining <= 0:
                self.active = False
                self.turns_until = self.rng.randint(18, 25)
            elif not in_shelter:
                fov_penalty = 2
        else:
            self.turns_until -= 1
            if self.turns_until <= 0:
                self.active = True
                self.remaining = self.rng.randint(3, 6)
                if not in_shelter:
                    fov_penalty = 2
        return self.active, fov_penalty

    def ambient_penalty(self) -> float:
        return 0.2 if self.active else 0.0
