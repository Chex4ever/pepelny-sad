"""Per-frame performance timers for the F4 debug overlay."""

from __future__ import annotations



import os

import time

from collections import deque

from contextlib import contextmanager

from typing import Iterator



# Timer keys → Russian labels (F4 profile section).

STAGE_LABELS: dict[str, str] = {

    "chunks_stream": "Стриминг чанков",

    "chunk_gen": "Генерация чанка",

    "fov": "FOV (всего)",

    "fov_los": "FOV: LOS",

    "fov_mark": "FOV: explored",

    "fov_ambient": "FOV: ambient",

    "ow_update": "Update overworld",

    "map_light": "Карта: light map",
    "map_shadow": "Карта: тени",

    "map_queue": "Карта: draw queue",

    "map_fog": "Карта: fog",

    "map_draw": "Карта: в буфер",

    "status": "HUD строка",

    "windows": "Окна UI",

    "ow_draw": "Draw overworld",

    "overlay_ui": "Оверлей F1/F4",

    "present": "Present",

    "ow_input": "Overworld input",

    "gpu_map": "GPU: карта",

    "gpu_ui": "GPU: UI буфер",

    "gpu_swap": "GPU: swap",

    "display_ms": "GPU: flip",

    "loading_step": "Загрузка: шаг",

    "audio": "Аудио",

}





def perf_verbose_log() -> bool:

    """Log slow frames to stderr when PEPELNY_PERF=1."""

    return os.environ.get("PEPELNY_PERF", "").strip().lower() in ("1", "true", "yes")





class PerfStats:

    def __init__(self, history: int = 120) -> None:

        self._history: deque[float] = deque(maxlen=history)

        self._timers: dict[str, float] = {}

        self._counters: dict[str, int] = {}

        self._frame_start = 0.0

        self.last_frame_ms = 0.0



    def begin_frame(self) -> None:

        self._frame_start = time.perf_counter()

        self._timers.clear()

        self._counters.clear()



    def end_frame(self) -> None:

        self.last_frame_ms = (time.perf_counter() - self._frame_start) * 1000.0

        self._history.append(self.last_frame_ms)

        if perf_verbose_log() and self.last_frame_ms >= 50.0:

            for line in self.profile_lines()[:8]:

                print(f"[perf] {line}")



    @contextmanager

    def measure(self, name: str) -> Iterator[None]:

        t0 = time.perf_counter()

        try:

            yield

        finally:

            elapsed = (time.perf_counter() - t0) * 1000.0

            self._timers[name] = self._timers.get(name, 0.0) + elapsed



    def counter(self, name: str, n: int = 1) -> None:

        self._counters[name] = self._counters.get(name, 0) + n



    def set_counter(self, name: str, value: int) -> None:

        self._counters[name] = value



    def timer_ms(self, name: str) -> float:

        return self._timers.get(name, 0.0)



    def count(self, name: str) -> int:

        return self._counters.get(name, 0)



    def avg_frame_ms(self) -> float:

        if not self._history:

            return self.last_frame_ms

        return sum(self._history) / len(self._history)



    def p95_frame_ms(self) -> float:

        if not self._history:

            return self.last_frame_ms

        ordered = sorted(self._history)

        idx = min(len(ordered) - 1, int(len(ordered) * 0.95))

        return ordered[idx]



    def avg_fps(self) -> float:

        avg = self.avg_frame_ms()

        return 1000.0 / avg if avg > 0.01 else 0.0



    def profile_lines(self, *, max_rows: int = 14) -> list[str]:

        """Sorted stage breakdown (% of last frame; nested timers may overlap)."""

        frame = max(self.last_frame_ms, 0.01)

        items = [(k, ms) for k, ms in self._timers.items() if ms >= 0.05]

        items.sort(key=lambda x: -x[1])

        lines = [f"── Профиль кадра ({frame:.0f} ms) ──"]

        for key, ms in items[:max_rows]:

            label = STAGE_LABELS.get(key, key)

            pct = 100.0 * ms / frame

            lines.append(f"  {label:<20} {ms:6.1f} ms  {pct:4.0f}%")

        accounted = sum(ms for _, ms in items)

        gap = frame - accounted

        if gap > 1.0 and len(items) > 0:

            lines.append(f"  {'прочее':<20} {gap:6.1f} ms  {100.0 * gap / frame:4.0f}%")

        cnt_parts: list[str] = []

        for cname, label in (

            ("chunks_new", "чанков+"),

            ("draw_queue", "queue"),

            ("gpu_batch", "gpu_q"),

            ("ui_quads", "ui_q"),

            ("get_column", "cols"),

            ("get_column_hit", "col_hit"),

        ):

            v = self.count(cname)

            if v:

                cnt_parts.append(f"{label}={v}")

        if cnt_parts:

            lines.append("  " + "  ".join(cnt_parts))

        return lines



    def debug_lines(

        self,

        clock_fps: float,

        *,

        render_mode: str,

        render_label: str = "",

        loaded_chunks: int = 0,

        gpu_fallback: bool = False,

    ) -> list[str]:

        avg = self.avg_frame_ms()

        p95 = self.p95_frame_ms()

        lines = [

            f"Frame: {self.last_frame_ms:.1f} ms  avg {avg:.1f}  p95 {p95:.1f}",

            f"FPS clock: {clock_fps:.1f}  est: {self.avg_fps():.1f}",

            (

                f"Рендер: {render_label or render_mode}"

                + (f"  [{render_mode}]" if render_label and render_mode not in render_label else "")

                + f"  chunks: {loaded_chunks}"

            ),

        ]

        lines.extend(self.profile_lines())

        if render_mode == "gpu" or self.timer_ms("gpu_map") > 0:

            fb = " (CPU fallback)" if gpu_fallback else ""

            lines.append(f"  GPU fallback:{fb or ' нет'}")

        return lines


