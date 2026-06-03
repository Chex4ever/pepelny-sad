"""Bullet hell patterns and bullets."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    char: str = "|"
    alive: bool = True


class BulletPattern:
    def __init__(self, pattern_id: str, box_w: float, box_h: float, speed_mult: float = 1.0):
        self.pattern_id = pattern_id
        self.box_w = box_w
        self.box_h = box_h
        self.speed_mult = speed_mult
        self.bullets: list[Bullet] = []
        self.timer = 0
        self.done = False
        self.duration = 180
        self.reveal_tell = False

    def update(self):
        self.timer += 1
        if self.timer > self.duration:
            self.done = True
        for b in self.bullets:
            if not b.alive:
                continue
            b.x += b.vx * self.speed_mult
            b.y += b.vy * self.speed_mult
            if b.x < -2 or b.x > self.box_w + 2 or b.y < -2 or b.y > self.box_h + 2:
                b.alive = False
        self._spawn()

    def _spawn(self):
        if self.pattern_id == "rain":
            if self.timer % 8 == 0:
                x = random.uniform(0, self.box_w)
                self.bullets.append(Bullet(x, -1, 0, 0.35, "|"))
        elif self.pattern_id == "sides":
            if self.timer % 20 == 0:
                self.bullets.append(Bullet(-1, self.box_h / 2, 0.4, 0, ">"))
                self.bullets.append(Bullet(self.box_w + 1, self.box_h / 2, -0.4, 0, "<"))
        elif self.pattern_id == "spiral":
            if self.timer % 6 == 0:
                ang = self.timer * 0.15
                cx, cy = self.box_w / 2, self.box_h / 2
                self.bullets.append(
                    Bullet(cx, cy, math.cos(ang) * 0.25, math.sin(ang) * 0.25, ".")
                )

    def active_bullets(self):
        return [b for b in self.bullets if b.alive]


def check_hit(soul_x: float, soul_y: float, soul_r: float, bullets: list[Bullet]) -> bool:
    for b in bullets:
        if not b.alive:
            continue
        dx = b.x - soul_x
        dy = b.y - soul_y
        if dx * dx + dy * dy < (soul_r + 0.3) ** 2:
            return True
    return False
