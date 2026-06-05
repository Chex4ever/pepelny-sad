"""Automated overworld playthrough benchmark (update → input → draw → present)."""
from __future__ import annotations

import json
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from src.constants import TARGET_FRAME_MS
from src.core.perf_stats import STAGE_LABELS, PerfStats
from src.render.render_mode import init_render_mode_from_env, render_mode


class BenchInput(Protocol):
    def begin_frame(self) -> None: ...
    def dir_key(self) -> tuple[int, int] | None: ...


@dataclass(frozen=True)
class OverworldBenchConfig:
    seed: int = 4242
    warmup_frames: int = 15
    measure_frames: int = 45
    dt_ms: int = 50
    bootstrap_new_game: bool = True
    walk_screen: str = "down"  # up|down|left|right — held each frame (iso-aware via InputState)


@dataclass
class PerfStageStats:
    key: str
    label: str
    mean_ms: float
    max_ms: float
    share_pct: float


@dataclass
class OverworldPerfReport:
    render_mode: str
    seed: int
    frames_total: int
    frames_measured: int
    player_start: tuple[int, int]
    player_end: tuple[int, int]
    chunks_loaded: int
    mean_frame_ms: float
    p95_frame_ms: float
    max_frame_ms: float
    stages: list[PerfStageStats] = field(default_factory=list)
    counters_mean: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def text_lines(self) -> list[str]:
        lines = [
            f"=== Overworld benchmark ({self.render_mode}) seed={self.seed} ===",
            f"Frames: {self.frames_measured} measured / {self.frames_total} total",
            f"Player: {self.player_start} -> {self.player_end}  chunks={self.chunks_loaded}",
            f"Frame: mean {self.mean_frame_ms:.1f} ms  p95 {self.p95_frame_ms:.1f}  max {self.max_frame_ms:.1f}",
            "--- stages (mean ms, % of frame) ---",
        ]
        for s in self.stages[:16]:
            lines.append(f"  {s.label:<22} {s.mean_ms:7.1f} ms  {s.share_pct:5.1f}%")
        if self.counters_mean:
            cnt = "  ".join(f"{k}={v:.1f}" for k, v in sorted(self.counters_mean.items()))
            lines.append(f"--- counters (mean/frame) ---")
            lines.append(f"  {cnt}")
        return lines


def _walk_keys(screen: str) -> set[int]:
    import pygame

    mapping = {
        "up": {pygame.K_UP, pygame.K_w},
        "down": {pygame.K_DOWN, pygame.K_s},
        "left": {pygame.K_LEFT, pygame.K_a},
        "right": {pygame.K_RIGHT, pygame.K_d},
    }
    return mapping.get(screen, mapping["down"])


class WalkInput:
    """Held movement key every frame (uses real InputState dir_key / iso)."""

    def __init__(self, screen_dir: str = "down") -> None:
        from src.input import InputState

        self._inner = InputState()
        self._keys = _walk_keys(screen_dir)

    def begin_frame(self) -> None:
        from src.input import _KEY_SCANCODES

        self._inner.begin_frame()
        for key in self._keys:
            self._inner.keys_pressed.add(key)
            self._inner.keys_down.add(key)
            sc = _KEY_SCANCODES.get(key)
            if sc is not None:
                self._inner.scancodes_pressed.add(sc)
                self._inner.scancodes_down.add(sc)

    def dir_key(self) -> tuple[int, int] | None:
        return self._inner.dir_key()

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def bootstrap_bench_world(game: Any, seed: int) -> None:
    """Like starting a new game: profile, chunks, overworld scene."""
    from src.core.new_game_loader import iter_build_new_game

    for _ in iter_build_new_game(game, seed):
        pass
    if game.world_map.perf_stats is None:
        game.world_map.perf_stats = game.perf


def run_overworld_frame(
    game: Any,
    inp: BenchInput,
    *,
    dt_ms: int = 16,
    gpu_present: bool = False,
) -> float:
    """One frame matching in-game overworld order (with perf timers)."""
    ow = game.overworld
    perf: PerfStats = game.perf
    perf.begin_frame()
    ow.handle_input(inp, dt_ms)
    ow.prepare_draw(dt_ms)
    ow.draw(game.buffer, inp)
    ow.update_deferred(dt_ms)
    if gpu_present and getattr(game, "gpu_presenter", None) is not None:
        with perf.measure("present"):
            game.gpu_presenter.render_overworld(game)
    perf.end_frame()
    return perf.last_frame_ms


def run_overworld_playthrough(
    game: Any,
    config: OverworldBenchConfig | None = None,
    *,
    inp: BenchInput | None = None,
    gpu_present: bool = False,
) -> OverworldPerfReport:
    """Walk in one direction; profile FOV, chunk gen, map build, and present."""
    cfg = config or OverworldBenchConfig()
    init_render_mode_from_env()
    mode = render_mode()

    if cfg.bootstrap_new_game:
        bootstrap_bench_world(game, cfg.seed)

    ow = game.overworld
    start_pos = ow.player.tile_pos()
    walk_inp = inp or WalkInput(cfg.walk_screen)

    frame_samples: list[float] = []
    timer_accum: dict[str, list[float]] = {}
    counter_accum: dict[str, list[int]] = {}
    total = cfg.warmup_frames + cfg.measure_frames

    for i in range(total):
        walk_inp.begin_frame()
        ms = run_overworld_frame(game, walk_inp, dt_ms=cfg.dt_ms, gpu_present=gpu_present)
        if i >= cfg.warmup_frames:
            frame_samples.append(ms)
            for key, val in game.perf._timers.items():
                timer_accum.setdefault(key, []).append(val)
            for key, val in game.perf._counters.items():
                counter_accum.setdefault(key, []).append(val)

    mean_frame = statistics.mean(frame_samples) if frame_samples else 0.0
    ordered = sorted(frame_samples)
    p95 = ordered[int(len(ordered) * 0.95)] if ordered else 0.0

    stages: list[PerfStageStats] = []
    for key, vals in timer_accum.items():
        mean_t = statistics.mean(vals)
        stages.append(
            PerfStageStats(
                key=key,
                label=STAGE_LABELS.get(key, key),
                mean_ms=mean_t,
                max_ms=max(vals),
                share_pct=100.0 * mean_t / max(mean_frame, 0.01),
            )
        )
    stages.sort(key=lambda s: -s.mean_ms)

    counters_mean = {k: statistics.mean(v) for k, v in counter_accum.items()}

    return OverworldPerfReport(
        render_mode=mode,
        seed=cfg.seed,
        frames_total=total,
        frames_measured=len(frame_samples),
        player_start=start_pos,
        player_end=ow.player.tile_pos(),
        chunks_loaded=len(game.world_map.chunks),
        mean_frame_ms=mean_frame,
        p95_frame_ms=p95,
        max_frame_ms=max(frame_samples) if frame_samples else 0.0,
        stages=stages,
        counters_mean=counters_mean,
    )


def default_fov_los_budget_ms() -> float:
    """Mean fov_los stage budget (shadowcast at visible LOS radius)."""
    return float(os.environ.get("PEPELNY_FOV_LOS_MS", "10"))


def default_frame_budget_ms() -> tuple[float, float]:
    """Gameplay frame budget (full frame including GPU present). 60 FPS target."""
    mean_env = os.environ.get("PEPELNY_PERF_MEAN_MS")
    p95_env = os.environ.get("PEPELNY_PERF_P95_MS")
    if mean_env and p95_env:
        return float(mean_env), float(p95_env)
    return 16.0, 24.0


def default_gpu_map_budget_ms() -> float:
    """GPU iso draw (gpu_map stage), must fit inside frame budget."""
    return float(os.environ.get("PEPELNY_GPU_MAP_MS", "16"))


def default_gpu_batch_budget() -> int:
    """Max textured quads per overworld frame (gpu_batch counter)."""
    return int(os.environ.get("PEPELNY_GPU_BATCH_MAX", "8000"))


def default_budget_ms(render_mode: str) -> tuple[float, float]:
    """Mean / p95 frame budget. GPU gameplay path uses 16/24 ms; iso CPU is debug-only."""
    if render_mode == "iso" and os.environ.get("PEPELNY_TEST_ISO_CPU", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return 165.0, 260.0
    return default_frame_budget_ms()


def write_perf_report(report: OverworldPerfReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def maybe_write_report(report: OverworldPerfReport) -> Path | None:
    out = os.environ.get("PEPELNY_PERF_REPORT", "").strip()
    if not out:
        return None
    return write_perf_report(report, out)
