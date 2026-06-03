"""Title screen with phased intro animation."""
from __future__ import annotations

import math
import random

from src.constants import COLOR_GRASS_FG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TORCH
from src.render.screen_buffer import FOG_NONE, ScreenBuffer

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

PHASE_BORDER_MS = 1000
PHASE_TEXT_MS = 1000
PHASE_BG_MS = 3000


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class TitleScreen:
    def __init__(self):
        self._stars: list[tuple[int, int, float]] = []
        self._ash: list[tuple[float, float, float, str]] = []
        self._seed = 0
        self.start_ms = 0
        self._clock_started = False

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

    def _phase(self, elapsed_ms: int) -> tuple[str, float]:
        if elapsed_ms < PHASE_BORDER_MS:
            return "border", elapsed_ms / PHASE_BORDER_MS
        if elapsed_ms < PHASE_BORDER_MS + PHASE_TEXT_MS:
            return "text", (elapsed_ms - PHASE_BORDER_MS) / PHASE_TEXT_MS
        if elapsed_ms < PHASE_BORDER_MS + PHASE_TEXT_MS + PHASE_BG_MS:
            return "bg", (elapsed_ms - PHASE_BORDER_MS - PHASE_TEXT_MS) / PHASE_BG_MS
        return "done", 1.0

    def draw(self, buf: ScreenBuffer, seed: int, elapsed_ms: int, title_seed: int):
        w, h = buf.width, buf.height
        self._ensure_particles(seed, w, h)
        phase, t = self._phase(elapsed_ms)
        buf.clear(bg=(8, 8, 14))

        bg_alpha = int(255 * t) if phase in ("bg", "done") else 0
        text_alpha = int(255 * t) if phase in ("text", "bg", "done") else 0
        if phase == "done":
            bg_alpha = text_alpha = 255

        if bg_alpha > 0:
            self._draw_background(buf, seed, elapsed_ms // 16, w, h, bg_alpha)

        box_x, box_y, box_w, box_h = 24, 8, 52, 14
        if phase == "border":
            perimeter = 2 * (box_w + box_h)
            progress = int(perimeter * t)
            self._draw_border_progress(buf, box_x, box_y, box_w, box_h, progress)
        elif text_alpha > 0:
            panel_bg = (14, 18, 14, text_alpha)
            buf.draw_box(box_x, box_y, box_w, box_h, title="  ПЕПЕЛЬНЫЙ САД  ", fg=(90, 110, 90), bg=(14, 18, 14))
            buf.draw_text(28, 12, "Сад увядает. Пепел помнит.", fg=COLOR_TEXT_DIM, fg_a=text_alpha)
            buf.draw_text(28, 14, "Enter / клик — новая игра", fg=COLOR_TEXT, fg_a=text_alpha)
            buf.draw_text(28, 16, f"R — другой seed ({title_seed})", fg=COLOR_TEXT, fg_a=text_alpha)
            buf.draw_text(28, 18, "L — загрузить сохранение", fg=COLOR_TEXT, fg_a=text_alpha)
            buf.draw_text(30, 20, "Esc — выход", fg=COLOR_TEXT_DIM, fg_a=text_alpha)
            if text_alpha > 100:
                torch_y = box_y + box_h - 2
                torch_ch = "i" if (elapsed_ms // 80) % 2 else "l"
                buf.set(box_x + 2, torch_y, torch_ch, fg=COLOR_TORCH, bg=(14, 18, 14))
                buf.set(box_w + box_x - 3, torch_y, torch_ch, fg=COLOR_TORCH, bg=(14, 18, 14))

    def _draw_border_progress(self, buf, x, y, w, h, progress):
        pts = []
        for i in range(w):
            pts.append((x + i, y))
        for i in range(1, h):
            pts.append((x + w - 1, y + i))
        for i in range(w - 2, -1, -1):
            pts.append((x + i, y + h - 1))
        for i in range(h - 2, 0, -1):
            pts.append((x, y + i))
        for i, (px, py) in enumerate(pts[:progress]):
            ch = "─" if px not in (x, x + w - 1) else "│"
            if (px, py) == (x, y):
                ch = "┌"
            elif (px, py) == (x + w - 1, y):
                ch = "┐"
            elif (px, py) == (x, y + h - 1):
                ch = "└"
            elif (px, py) == (x + w - 1, y + h - 1):
                ch = "┘"
            buf.set(px, py, ch, fg=(100, 140, 100), bg=(8, 10, 8))

    def _draw_background(self, buf, seed, frame, w, h, bg_alpha):
        horizon_y = 16
        for y in range(horizon_y):
            sky_t = y / max(1, horizon_y - 1)
            sky = _lerp_color(SKY_TOP, SKY_HORIZON, sky_t ** 0.8)
            light = 0.45 + 0.55 * (1.0 - sky_t * 0.5)
            for x in range(w):
                buf.set(x, y, " ", bg=sky, light=light, bg_a=bg_alpha)

        for i, (sx, sy, base_light) in enumerate(self._stars):
            pulse = 0.65 + 0.35 * math.sin(frame * 0.04 + i * 0.7)
            ch = "*" if pulse > 0.85 else "+" if pulse > 0.6 else "·"
            if buf.in_bounds(sx, sy):
                buf.set(sx, sy, ch, fg=(210, 200, 170), bg=SKY_TOP, light=base_light * pulse, bg_a=bg_alpha, fg_a=bg_alpha)

        for y in range(horizon_y, horizon_y + 5):
            row_t = (y - horizon_y) / 4
            bg = _lerp_color(SKY_HORIZON, HILL_FG, row_t)
            for x in range(w):
                wave = int(3 * math.sin(x * 0.08 + y * 0.3 + seed * 0.01))
                if (x + wave + y) % 7 == 0:
                    buf.set(x, y, "^", fg=HILL_FG, bg=bg, light=0.35, bg_a=bg_alpha, fg_a=bg_alpha)
                else:
                    buf.set(x, y, " ", bg=bg, light=0.4, bg_a=bg_alpha)

        ground_y = horizon_y + 5
        for y in range(ground_y, h):
            depth = (y - ground_y) / max(1, h - ground_y - 1)
            bg = _lerp_color(GARDEN_BG, (18, 20, 16), depth * 0.6)
            for x in range(w):
                if (x * 3 + y * 5 + seed) % 11 == 0:
                    ch, fg = ":", ASH_DIM
                elif (x + y) % 5 == 0:
                    ch, fg = ",", GARDEN_FG
                else:
                    ch, fg = ".", COLOR_GRASS_FG
                buf.set(x, y, ch, fg=fg, bg=bg, light=0.55 + depth * 0.2, bg_a=bg_alpha, fg_a=bg_alpha)

        start_y = h - len(GARDEN_SILHOUETTE) - 1
        for row, line in enumerate(GARDEN_SILHOUETTE):
            y = start_y + row
            ox = max(0, (w - len(line)) // 2)
            for x, ch in enumerate(line):
                px = ox + x
                if not buf.in_bounds(px, y) or ch == " ":
                    continue
                fg = (60, 70, 55)
                if ch in "T|/\\":
                    fg = (55, 65, 50)
                elif ch in "~^":
                    fg = (70, 85, 65)
                buf.set(px, y, ch, fg=fg, bg=GARDEN_BG, light=0.5, bg_a=bg_alpha, fg_a=bg_alpha)

        if bg_alpha > 180:
            for i, (ax, ay, speed, ch) in enumerate(self._ash):
                px = (ax + math.sin(frame * 0.02 + i) * 2) % w
                py = (ay + frame * speed * 0.35) % (h - 4)
                if py < 10:
                    continue
                flicker = 0.5 + 0.5 * math.sin(frame * 0.08 + i * 1.3)
                if buf.in_bounds(int(px), int(py)):
                    buf.set_fg_only(int(px), int(py), ch, fg=ASH_FG, light=0.35 + 0.4 * flicker, fg_a=int(bg_alpha * 0.85))
