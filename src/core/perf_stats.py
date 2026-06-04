"""Lightweight per-frame performance counters for the debug overlay."""
from __future__ import annotations

import time
from collections import deque
from contextlib import contextmanager
from typing import Iterator


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

    def debug_lines(
        self, clock_fps: float, *, render_mode: str, loaded_chunks: int = 0
    ) -> list[str]:
        avg = self.avg_frame_ms()
        p95 = self.p95_frame_ms()
        lines = [
            f"Frame: {self.last_frame_ms:.1f} ms  avg {avg:.1f}  p95 {p95:.1f}",
            f"FPS clock: {clock_fps:.1f}  est: {self.avg_fps():.1f}",
            (
                f"  upd {self.timer_ms('ow_update'):.1f}  "
                f"draw {self.timer_ms('ow_draw'):.1f}  "
                f"fov {self.timer_ms('fov'):.1f}  "
                f"map {self.timer_ms('map_draw'):.1f}"
            ),
            (
                f"  cols {self.count('get_column')}  "
                f"hit {self.count('get_column_hit')}  "
                f"stamps {self.count('stamp')}  "
                f"q {self.count('draw_queue')}"
            ),
            f"Render: {render_mode}  chunks loaded: {loaded_chunks}",
        ]
        return lines
