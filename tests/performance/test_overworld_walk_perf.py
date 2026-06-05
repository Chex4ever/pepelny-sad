"""Walk overworld in one direction — profiles FOV, chunks, map, present."""
from __future__ import annotations

import pytest

from src.core.perf_benchmark import (
    default_budget_ms,
    default_fov_los_budget_ms,
    maybe_write_report,
    run_overworld_playthrough,
)
from src.render.render_mode import render_mode


@pytest.mark.performance
@pytest.mark.slow
def test_overworld_iso_walk_playthrough(bench_game_iso, bench_config):
    """Like in-game: new game, then hold S and walk (chunk streaming + FOV)."""
    report = run_overworld_playthrough(
        bench_game_iso,
        bench_config,
        gpu_present=False,
    )
    maybe_write_report(report)

    assert report.player_end != report.player_start, "player should move"
    assert report.chunks_loaded >= 4
    assert report.counters_mean.get("draw_queue", 0) > 0

    mean_budget, p95_budget = default_budget_ms("iso")
    assert report.mean_frame_ms < mean_budget, (
        f"mean {report.mean_frame_ms:.1f} ms > budget {mean_budget}\n"
        + "\n".join(report.text_lines()[:12])
    )
    assert report.p95_frame_ms < p95_budget, f"p95 {report.p95_frame_ms:.1f} ms"

    fov_budget = default_fov_los_budget_ms()
    fov_stage = next((s for s in report.stages if s.key == "fov_los"), None)
    if fov_stage is not None:
        assert fov_stage.mean_ms < fov_budget, (
            f"fov_los mean {fov_stage.mean_ms:.1f} ms > {fov_budget} ms"
        )

    top = report.stages[0].key if report.stages else ""
    assert top in (
        "present",
        "map_queue",
        "map_draw",
        "fov_los",
        "fov",
        "ow_update",
        "ow_draw",
        "gpu_map",
        "chunks_stream",
        "chunk_gen",
    )


@pytest.mark.performance
@pytest.mark.slow
def test_overworld_walk_reports_stage_timers(bench_game_iso, bench_config):
    """Ensure named perf stages are populated during walk."""
    report = run_overworld_playthrough(bench_game_iso, bench_config)
    keys = {s.key for s in report.stages}
    assert "fov_los" in keys or "fov" in keys
    assert "map_queue" in keys or "map_draw" in keys
    if report.counters_mean.get("chunks_new", 0) > 0:
        assert "chunk_gen" in keys or "chunks_stream" in keys

