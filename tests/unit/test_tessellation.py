"""Unit tests for diag iso-square tessellation."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_stamp_origin_is_diag_not_horiz_brick():
    from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

    assert stamp_tip(1, 0) == (1, 1)
    assert stamp_origin(1, 0) == (0, 0)
    assert stamp_origin(1, 0) != (2, 0)  # old horiz_brick


@pytest.mark.unit
def test_tile_neighbors_six():
    from src.prototype.dia_scale.tessellation import tile_neighbors

    n = tile_neighbors(3, 3)
    assert len(n) == 6
    assert len(set(n)) == 6
    assert (4, 3) in n
    assert (2, 3) in n
    assert (3, 4) in n
    assert (3, 2) in n
    assert (4, 2) in n
    assert (2, 4) in n


@pytest.mark.unit
def test_stamp_tip_is_diag_lattice():
    from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

    assert stamp_tip(1, 0) == (1, 1)
    assert stamp_origin(1, 0) == (0, 0)
    assert stamp_tip(2, 3) == (-1, 5)


@pytest.mark.unit
def test_tile_world_matches_iso_projector():
    from src.prototype.dia_scale.tessellation import stamp_tip
    from src.render.iso_projector import IsoProjector

    p = IsoProjector(origin_x=0, origin_y=0)
    for tx, ty in ((0, 0), (1, 0), (0, 1), (2, 3)):
        tip_x, tip_y = stamp_tip(tx, ty)
        su, sv = p._raw_screen(float(tip_x), float(tip_y))
        assert su == int(round((tip_x - tip_y) * 2))
        assert sv == int(round((tip_x + tip_y) * 1))


@pytest.mark.unit
def test_diag_2x2_stamp_sketch_has_no_internal_gaps():
    from src.prototype.dia_scale.tessellation import analyze_floor_coverage

    stats = analyze_floor_coverage(2, 2)
    assert stats.tiles == 4
    assert stats.filled_cells == 16
    assert stats.internal_gaps == 0
    assert stats.seams == 4


@pytest.mark.unit
def test_diag_2x2_sketch_reference():
    from src.prototype.dia_scale.tessellation import DIAG_2X2_SKETCH, analyze_floor_coverage

    assert len(DIAG_2X2_SKETCH) == 4
    stats = analyze_floor_coverage(2, 2)
    assert stats.tiles == 4
    assert stats.filled_cells == 16
    assert stats.internal_gaps == 0
    assert sum(ch != "_" for row in DIAG_2X2_SKETCH for ch in row) == 16
