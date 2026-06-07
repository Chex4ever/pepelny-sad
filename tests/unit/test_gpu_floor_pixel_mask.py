"""Pixel-level GPU floor artifact checks (bbox ears outside iso diamond)."""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BIOME_VIEWER = os.path.join(ROOT, "scripts", "biome_viewer.py")


def _load_biome_viewer():
    spec = importlib.util.spec_from_file_location("biome_viewer", _BIOME_VIEWER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["biome_viewer"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def biome_viewer():
    return _load_biome_viewer()


def _gpu_meadow_surface(
    biome_viewer,
    *,
    w: int,
    h: int,
    seed: int,
    focus_wx: int,
    focus_wy: int,
    floor_mode: str = "undercoat",
):
    from src.constants import init_paths
    from src.tools.iso_preview import (
        OverworldPreview,
        build_surface_draw_queue,
        floor_tile_geom_bounds,
        gpu_surface_footprint_pixel_artifacts,
    )

    init_paths(ROOT)
    import pygame

    pygame.init()
    try:
        chunk = biome_viewer.generate_patch(
            0, 0, w, h, seed, forced_biome="meadow", trees=False
        )
        queue = build_surface_draw_queue(chunk, 0, 0, w, h)
        preview = OverworldPreview("gpu")
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        surf = preview.capture(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        bounds = floor_tile_geom_bounds(
            queue, focus_wx=focus_wx, focus_wy=focus_wy
        )
        ears, holes = gpu_surface_footprint_pixel_artifacts(surf, bounds)
        preview.release()
        return surf, queue, bounds, ears, holes
    finally:
        pygame.quit()


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_single_tile_gpu_no_footprint_ear_pixels(monkeypatch, biome_viewer):
    """One grass tile: pixels outside iso diamond must stay COLOR_BG (no AABB ears)."""
    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.setenv("PEPELNY_RENDER", "gpu")
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "1")
    monkeypatch.setenv("PEPELNY_GPU_FLOOR_MODE", "undercoat")

    from src.constants import init_paths
    from src.tools.iso_preview import (
        OverworldPreview,
        build_footprint_mask_surface,
        floor_tile_geom_bounds,
        gpu_surface_footprint_pixel_artifacts,
        is_gpu_clear_pixel,
    )

    init_paths(ROOT)
    import pygame

    pygame.init()
    try:
        focus_wx, focus_wy = 10, 10
        queue = [
            (0, focus_wx, focus_wy, 0.0, "grass", (40, 120, 40), (20, 40, 20), 1.0, 0),
        ]
        preview = OverworldPreview("gpu")
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        surf = preview.capture(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        bounds = floor_tile_geom_bounds(
            queue, focus_wx=focus_wx, focus_wy=focus_wy
        )
        assert len(bounds) == 1

        mask = build_footprint_mask_surface(
            bounds, width=surf.get_width(), height=surf.get_height()
        )
        ears, holes = gpu_surface_footprint_pixel_artifacts(surf, bounds)
        assert ears == [], f"{len(ears)} ear pixels, e.g. {ears[:12]}"

        # Mask sanity: outside=white diamond only; framebuffer ears must be bg.
        x0, y0, x1, y1 = bounds[0]
        for py in range(int(y0), int(y1)):
            for px in range(int(x0), int(x1)):
                in_mask = mask.get_at((px, py))[0] > 128
                r, g, b, *_ = surf.get_at((px, py))
                if not in_mask:
                    assert is_gpu_clear_pixel((r, g, b)), (
                        f"outside mask painted at {(px, py)} rgb={(r, g, b)}"
                    )

        # Solid undercoat: no framebuffer-bg holes inside the diamond.
        assert holes == [], f"{len(holes)} bg holes inside diamond, e.g. {holes[:12]}"
        preview.release()
    finally:
        pygame.quit()


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
@pytest.mark.parametrize("floor_mode", ["undercoat", "opaque_splat"])
def test_meadow_preview_14x14_gpu_no_ear_pixels(
    monkeypatch, biome_viewer, floor_mode
):
    """Same patch as scripts/meadow_preview.py (14x14 meadow seed=4242)."""
    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.setenv("PEPELNY_RENDER", "gpu")
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "1")
    monkeypatch.setenv("PEPELNY_GPU_FLOOR_MODE", floor_mode)

    _surf, _queue, _bounds, ears, holes = _gpu_meadow_surface(
        biome_viewer,
        w=14,
        h=14,
        seed=4242,
        focus_wx=7,
        focus_wy=7,
        floor_mode=floor_mode,
    )
    assert ears == [], f"meadow 14x14: {len(ears)} ear pixels, e.g. {ears[:12]}"
    assert holes == [], f"meadow 14x14: {len(holes)} bg holes, e.g. {holes[:12]}"

