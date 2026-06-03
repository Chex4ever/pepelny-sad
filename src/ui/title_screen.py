"""Title screen background — пепел, закат, увядший сад."""
from __future__ import annotations

import math
import random

from src.constants import (
    COLOR_BG,
    COLOR_GRASS,
    COLOR_GRASS_FG,
    COLOR_HIGHLIGHT,
    COLOR_SURFACE_SKY,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_TORCH,
)
from src.render.screen_buffer import ScreenBuffer

# Силуэт сада (центр экрана, нижняя треть)
GARDEN_SILHOUETTE = [
    "                              ~^~                 ~^~                    ",
    "                             /...\\               /...\\                   ",
    "                              ~~~                 ~~~                     ",
    "           T                              T              T                ",
    "          /|\\                            /|\\            /|\\               ",
    "         / | \\                          / | \\          / | \\              ",
    "        ~~~~~~~                        ~~~~~~~        ~~~~~~~             ",
    "   ==================================================================   ",
    "  ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,  ",
    " , : . , : . , : . , : . , : . , : . , : . , : . , : . , : . , : . , : ",
]

SKY_TOP = (18, 14, 32)
SKY_HORIZON = (55, 42, 38)
ASH_FG = (140, 130, 120)
ASH_DIM = (90, 85, 80)
GARDEN_FG = (95, 110, 85)
GARDEN_BG = (28, 32, 26)
HILL_FG = (45, 50, 42)


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class TitleScreen:
    def __init__(self):
        self._stars: list[tuple[int, int, float]] = []
        self._ash: list[tuple[float, float, float, str]] = []
        self._seed = 0

    def _ensure_particles(self, seed: int, width: int, height: int):
        if self._seed == seed and self._stars:
            return
        self._seed = seed
        rng = random.Random(seed ^ 0xA5ED)
        self._stars = [
            (rng.randint(0, width - 1), rng.randint(0, 11), rng.uniform(0.4, 1.0))
            for _ in range(55)
        ]
        self._ash = [
            (
                rng.uniform(0, width),
                rng.uniform(8, height - 6),
                rng.uniform(0.15, 0.55),
                rng.choice([":", "·", ".", "`", "'"]),
            )
            for _ in range(120)
        ]

    def draw(self, buf: ScreenBuffer, seed: int, frame: int, title_seed: int):
        w, h = buf.width, buf.height
        self._ensure_particles(seed, w, h)

        # Небо — закат над пепельными степями
        horizon_y = 16
        for y in range(horizon_y):
            t = y / max(1, horizon_y - 1)
            sky = _lerp_color(SKY_TOP, SKY_HORIZON, t ** 0.8)
            light = 0.45 + 0.55 * (1.0 - t * 0.5)
            for x in range(w):
                buf.set(x, y, " ", bg=sky, light=light)

        # Звёзды / искры (мерцание)
        for i, (sx, sy, base_light) in enumerate(self._stars):
            pulse = 0.65 + 0.35 * math.sin(frame * 0.04 + i * 0.7)
            ch = "*" if pulse > 0.85 else "+" if pulse > 0.6 else "·"
            if buf.in_bounds(sx, sy):
                buf.set(sx, sy, ch, fg=(210, 200, 170), bg=SKY_TOP, light=base_light * pulse)

        # Дальние холмы
        for y in range(horizon_y, horizon_y + 5):
            row_t = (y - horizon_y) / 4
            bg = _lerp_color(SKY_HORIZON, HILL_FG, row_t)
            for x in range(w):
                wave = int(3 * math.sin(x * 0.08 + y * 0.3 + seed * 0.01))
                if (x + wave + y) % 7 == 0:
                    buf.set(x, y, "^", fg=HILL_FG, bg=bg, light=0.35)
                else:
                    buf.set(x, y, " ", bg=bg, light=0.4)

        # Земля — серая трава
        ground_y = horizon_y + 5
        for y in range(ground_y, h):
            depth = (y - ground_y) / max(1, h - ground_y - 1)
            bg = _lerp_color(GARDEN_BG, (18, 20, 16), depth * 0.6)
            for x in range(w):
                if (x * 3 + y * 5 + seed) % 11 == 0:
                    ch = ":"
                    fg = ASH_DIM
                elif (x + y) % 5 == 0:
                    ch = ","
                    fg = GARDEN_FG
                else:
                    ch = "."
                    fg = COLOR_GRASS_FG
                buf.set(x, y, ch, fg=fg, bg=bg, light=0.55 + depth * 0.2)

        # Силуэт сада
        start_y = h - len(GARDEN_SILHOUETTE) - 1
        for row, line in enumerate(GARDEN_SILHOUETTE):
            y = start_y + row
            ox = max(0, (w - len(line)) // 2)
            for x, ch in enumerate(line):
                px = ox + x
                if not buf.in_bounds(px, y) or ch == " ":
                    continue
                if ch in "T|/\\":
                    fg = (55, 65, 50)
                    light = 0.45
                elif ch in "~^":
                    fg = (70, 85, 65)
                    light = 0.5
                elif ch == "=":
                    fg = (80, 75, 70)
                    light = 0.4
                elif ch in ",:":
                    fg = GARDEN_FG
                    light = 0.55
                else:
                    fg = (60, 70, 55)
                    light = 0.45
                buf.set(px, y, ch, fg=fg, bg=GARDEN_BG, light=light)

        # Падающий пепел
        for i, (ax, ay, speed, ch) in enumerate(self._ash):
            px = (ax + math.sin(frame * 0.02 + i) * 2) % w
            py = (ay + frame * speed * 0.35) % (h - 4)
            if py < 10:
                continue
            flicker = 0.5 + 0.5 * math.sin(frame * 0.08 + i * 1.3)
            if buf.in_bounds(int(px), int(py)):
                buf.set(int(px), int(py), ch, fg=ASH_FG, bg=COLOR_BG, light=0.35 + 0.4 * flicker)

        # Лёгкая дымка поверх поля
        for y in range(ground_y, h - 8, 3):
            for x in range(0, w, 4):
                if (x + y + frame // 8) % 9 == 0:
                    buf.set(x, y, ":", fg=ASH_DIM, bg=buf.bg[buf._idx(x, y)], light=0.25)

        # Меню — читаемая панель
        box_x, box_y, box_w, box_h = 24, 8, 52, 14
        buf.draw_box(box_x, box_y, box_w, box_h, title="  ПЕПЕЛЬНЫЙ САД  ", fg=(90, 110, 90), bg=(14, 18, 14))
        buf.draw_text(28, 12, "Сад увядает. Пепел помнит.", fg=COLOR_TEXT_DIM)
        buf.draw_text(28, 14, "Enter / клик — новая игра", fg=COLOR_TEXT)
        buf.draw_text(28, 16, f"R — другой seed ({title_seed})", fg=COLOR_TEXT)
        buf.draw_text(28, 18, "L — загрузить сохранение", fg=COLOR_TEXT)
        buf.draw_text(30, 20, "Esc — выход", fg=COLOR_TEXT_DIM)

        # Маленький факел у рамки (мерцание)
        torch_y = box_y + box_h - 2
        torch_ch = "i" if (frame // 5) % 2 else "l"
        torch_light = 0.7 + 0.3 * math.sin(frame * 0.15)
        buf.set(box_x + 2, torch_y, torch_ch, fg=COLOR_TORCH, bg=(14, 18, 14), light=torch_light)
        buf.set(box_w + box_x - 3, torch_y, torch_ch, fg=COLOR_TORCH, bg=(14, 18, 14), light=torch_light)
