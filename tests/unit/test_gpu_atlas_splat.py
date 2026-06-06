"""Atlas splat: one GPU quad per floor tile."""
from __future__ import annotations

import os

import pytest

from src.render.gpu.context import gl_available
from src.render.gpu.iso_renderer import GpuIsoRenderer, gpu_floor_mode, gpu_splat_enabled


@pytest.fixture
def iso_renderer(monkeypatch):
    if not gl_available():
        pytest.skip("No OpenGL context")
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "1")
    monkeypatch.delenv("PEPELNY_BENCH", raising=False)
    import moderngl

    ctx = moderngl.create_context(standalone=True)
    from src.render.gpu.context import GpuContext

    gpu = GpuContext(ctx=ctx, width=800, height=600)
    renderer = GpuIsoRenderer(gpu)
    try:
        yield renderer
    finally:
        renderer.release()
        ctx.release()


def test_gpu_splat_enabled_default(monkeypatch):
    monkeypatch.delenv("PEPELNY_GPU_SPLAT", raising=False)
    assert gpu_splat_enabled() is True
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "0")
    assert gpu_splat_enabled() is False


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_floor_tiles_undercoat_plus_splat(iso_renderer):
    """N floor tiles → 2N quads (solid undercoat + diamond splat), not per-glyph."""
    queue = [
        (0, 10, 10, 0.0, "grass", (40, 120, 40), (20, 40, 20), 1.0, 0),
        (1, 11, 10, 0.0, "grass_dry", (100, 90, 50), (40, 35, 20), 1.0, 0),
        (2, 12, 11, 0.0, "ridge", (80, 80, 80), (30, 30, 30), 1.0, 0),
    ]
    iso_renderer.draw(queue, focus_wx=11, focus_wy=10)
    assert iso_renderer.last_batch_quads == 2 * len(queue)


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_tree_stencil_one_quad_with_splat(iso_renderer):
    queue = [
        (0, 10, 10, 1.5, "tree", (40, 120, 40), (20, 40, 20), 1.0, 0),
    ]
    iso_renderer.draw(queue, focus_wx=10, focus_wy=10)
    assert iso_renderer.last_batch_quads == 1


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_legacy_path_more_quads_without_splat(iso_renderer, monkeypatch):
    monkeypatch.setenv("PEPELNY_GPU_SPLAT", "0")
    queue = [
        (0, 10, 10, 0.0, "grass", (40, 120, 40), (20, 40, 20), 1.0, 0),
    ]
    iso_renderer.draw(queue, focus_wx=10, focus_wy=10)
    assert iso_renderer.last_batch_quads > 1


def test_gpu_floor_mode_default_undercoat(monkeypatch):
    monkeypatch.delenv("PEPELNY_GPU_FLOOR_MODE", raising=False)
    assert gpu_floor_mode() == "undercoat"


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_opaque_splat_floor_undercoat_plus_baked_splat(iso_renderer, monkeypatch):
    """opaque_splat: clipped undercoat + diamond splat:id (no bbox ear bleed)."""
    monkeypatch.setenv("PEPELNY_GPU_FLOOR_MODE", "opaque_splat")
    queue = [
        (0, 10, 10, 0.0, "grass", (40, 120, 40), (20, 40, 20), 1.0, 0),
        (1, 11, 10, 0.0, "grass_dry", (100, 90, 50), (40, 35, 20), 1.0, 0),
    ]
    iso_renderer.draw(queue, focus_wx=11, focus_wy=10)
    assert iso_renderer.last_batch_quads == 2 * len(queue)


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_glyphs_floor_mode_per_glyph(iso_renderer, monkeypatch):
    monkeypatch.setenv("PEPELNY_GPU_FLOOR_MODE", "glyphs")
    queue = [
        (0, 10, 10, 0.0, "grass", (40, 120, 40), (20, 40, 20), 1.0, 0),
    ]
    iso_renderer.draw(queue, focus_wx=10, focus_wy=10)
    assert iso_renderer.last_batch_quads > 1
