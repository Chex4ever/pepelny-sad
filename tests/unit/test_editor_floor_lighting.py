"""Tests for editor floor patch and lighting."""
from __future__ import annotations

import math

import pytest


@pytest.mark.unit
def test_floor_patch_diag_iso_coverage():
    from src.characters.editor_floor import (
        build_floor_patch,
        floor_screen_offset,
        floor_patch_bounds,
        floor_solid_char_cells,
        floor_solid_has_internal_holes,
    )

    cells = build_floor_patch(10, 20, seed=7)
    solid = floor_solid_char_cells(10, 20)
    assert len(cells) == len(solid)
    assert floor_solid_has_internal_holes(10, 20) == []

    min_u, max_u, min_v, max_v = floor_patch_bounds(cells, 10, 20)
    assert max_u - min_u + 1 >= 5
    assert max_v - min_v + 1 >= 5
    assert floor_screen_offset(10, 20, ref_cx=10, ref_cy=20) == (0, 0)


@pytest.mark.unit
def test_sun_elevation_and_azimuth():
    from src.characters.editor_lighting import EditorLighting, brightness_at

    lit = EditorLighting()
    assert 40.0 < lit.elevation_deg < 50.0
    b_zenith = brightness_at(0.0, 0.0, 1.0, lighting=lit)

    lit.nudge_elevation(20.0)
    assert lit.elevation_deg > 60.0
    b_higher = brightness_at(0.0, 0.0, 1.0, lighting=lit)
    assert b_higher >= b_zenith

    az0 = lit.azimuth_deg
    lit.nudge_azimuth(45.0)
    assert abs(lit.azimuth_deg - az0 - 45.0) < 0.01 or abs(lit.azimuth_deg - az0 + 315.0) < 0.01

    lx, ly, lz = lit.normalized_dir()
    assert math.isclose(lx * lx + ly * ly + lz * lz, 1.0, rel_tol=1e-5)
    assert lz > 0.5


@pytest.mark.unit
def test_sun_w_raises_elevation_s_lowers():
    from src.characters.editor_lighting import EditorLighting

    lit = EditorLighting()
    e0 = lit.sun_elevation
    lit.nudge_elevation(10.0)
    assert lit.sun_elevation > e0
    lit.nudge_elevation(-15.0)
    assert lit.sun_elevation < e0


@pytest.mark.unit
def test_editor_state_has_lighting():
    from src.characters.editor_state import EditorState
    from src.characters.editor_lighting import EditorLighting

    st = EditorState()
    assert isinstance(st.lighting, EditorLighting)
