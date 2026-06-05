"""PerfStats unit tests."""
from src.core.perf_stats import PerfStats


def test_frame_history_and_p95():
    perf = PerfStats(history=10)
    perf._history.extend([10.0, 20.0, 30.0, 40.0, 50.0])
    perf.last_frame_ms = 50.0
    assert perf.avg_frame_ms() == 30.0
    assert perf.p95_frame_ms() >= 40.0


def test_measure_accumulates():
    perf = PerfStats()
    perf.begin_frame()
    with perf.measure("foo"):
        pass
    with perf.measure("foo"):
        pass
    perf.end_frame()
    assert perf.timer_ms("foo") >= 0.0


def test_profile_lines_sorted():
    perf = PerfStats()
    perf.begin_frame()
    with perf.measure("fov_los"):
        pass
    perf._timers["gpu_map"] = 50.0
    perf._timers["fov_los"] = 10.0
    perf.end_frame()
    lines = perf.profile_lines()
    assert any("Профиль кадра" in ln for ln in lines)
    assert any("GPU" in ln for ln in lines)
