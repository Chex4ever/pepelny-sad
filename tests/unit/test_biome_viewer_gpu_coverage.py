"""GPU biome_viewer path must cover meadow union like CPU (no background gaps)."""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SCRIPT = os.path.join(ROOT, "scripts", "biome_viewer.py")


def _load_viewer():
    spec = importlib.util.spec_from_file_location("biome_viewer", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["biome_viewer"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def biome_viewer():
    return _load_viewer()


@pytest.mark.unit
@pytest.mark.parametrize("floor_mode", ["undercoat", "opaque_splat"])
@pytest.mark.parametrize("biome_id", ["meadow", "ashen_forest", "ridge", "ruins_edge"])
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_forced_biome_gpu_no_render_gaps(monkeypatch, biome_viewer, biome_id, floor_mode):
    """Regression: splat-only GPU floor left visible background gaps (biome_viewer)."""
    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.setenv("PEPELNY_RENDER", "gpu")
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "1")
    monkeypatch.setenv("PEPELNY_GPU_FLOOR_MODE", floor_mode)

    from src.constants import init_paths
    from src.data.art_loader import load_biomes
    from src.tools.iso_preview import (
        OverworldPreview,
        analyze_queue_footprint,
        build_surface_draw_queue,
        drawn_floor_bbox_ear_cells,
        drawn_floor_footprint_cells,
        gpu_surface_bbox_ear_leaks,
        gpu_surface_bg_gaps,
    )

    if biome_id not in load_biomes():
        pytest.skip(f"biome {biome_id} missing")

    init_paths(ROOT)
    import pygame

    pygame.init()
    try:
        chunk = biome_viewer.generate_patch(
            0, 0, 12, 12, 4242, forced_biome=biome_id, trees=False
        )
        queue = build_surface_draw_queue(chunk, 0, 0, 12, 12)
        focus_wx, focus_wy = 6, 6
        holes, _, covered = analyze_queue_footprint(
            queue, focus_wx=focus_wx, focus_wy=focus_wy
        )
        assert holes == []

        preview = OverworldPreview("gpu")
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        surf = preview.capture(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        preview.release()

        drawable = drawn_floor_footprint_cells(
            queue, focus_wx=focus_wx, focus_wy=focus_wy
        )
        gaps = gpu_surface_bg_gaps(surf, drawable)
        assert gaps == [], f"{biome_id}: {len(gaps)} bg gaps, e.g. {gaps[:8]}"

        ears = drawn_floor_bbox_ear_cells(
            queue, focus_wx=focus_wx, focus_wy=focus_wy
        )
        leaks = gpu_surface_bbox_ear_leaks(surf, ears, covered=drawable)
        assert leaks == [], (
            f"{biome_id}: {len(leaks)} bbox ear leaks, e.g. {leaks[:8]}"
        )
    finally:
        pygame.quit()
