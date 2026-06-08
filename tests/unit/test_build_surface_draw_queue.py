"""build_surface_draw_queue uses chunk-local indices."""
from __future__ import annotations

import pytest

from src.constants import CHUNK_SIZE
from src.tools.iso_preview import build_surface_draw_queue
from src.world.chunk import Chunk


@pytest.mark.unit
def test_draw_queue_reads_correct_local_column():
    chunk = Chunk(0, 0)
    chunk.set(5, 0, ".", stencil_id="road")
    queue = build_surface_draw_queue(chunk, wx0=5, wy0=0, w=1, h=1)
    floor = [e for e in queue if e[3] == 0.0]
    assert len(floor) == 1
    assert floor[0][4] == "road"
    assert floor[0][1] == 5


@pytest.mark.unit
def test_draw_queue_legacy_patch_buffer():
    """biome_viewer stores patch at local (dx,dy) on Chunk(0,0)."""
    chunk = Chunk(0, 0)
    chunk.set(0, 0, ".", stencil_id="meadow")
    queue = build_surface_draw_queue(chunk, wx0=80, wy0=80, w=1, h=1)
    floor = [e for e in queue if e[3] == 0.0]
    assert floor[0][4] == "meadow"
