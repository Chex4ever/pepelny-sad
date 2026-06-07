"""Tests for iso floor layout helpers."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_floor_world_extent_1m():
    from src.prototype.dia_scale.iso_character_renderer import floor_tile_range, floor_world_extent
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    assert len(list(floor_tile_range())) == EDITOR_FLOOR_TILES
    x0, y0, x1, y1 = floor_world_extent(0, 0)
    assert x1 > x0
    assert y1 > y0


@pytest.mark.unit
def test_view_scale_nudge():
    from src.characters.editor_state import EditorState

    st = EditorState()
    assert st.view_scale == 1
    st.nudge_view_scale(1)
    assert st.view_scale == 2
    st.nudge_view_scale(10)
    assert st.view_scale == 4
    st.nudge_view_scale(-1)
    assert st.view_scale == 3
