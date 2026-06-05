"""GPU atlas smoke tests (skip without OpenGL)."""
from __future__ import annotations

import pytest

from src.render.gpu.context import gl_available


@pytest.mark.skipif(not gl_available(), reason="No OpenGL context")
def test_atlas_region_uv():
    import moderngl

    from src.render.gpu.atlas import TileAtlas

    ctx = moderngl.create_context(standalone=True)
    try:
        atlas = TileAtlas(ctx)
        reg = atlas.get_region("grass")
        assert 0.0 <= reg.u0 < reg.u1 <= 1.0
        assert 0.0 <= reg.v0 < reg.v1 <= 1.0
        assert atlas.region_count() >= 1
    finally:
        ctx.release()
