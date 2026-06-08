"""Alphabet 5×5 floor render matches 19×10 golden reference."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_alphabet_tile_letters_row_major():
    from src.engine.layout.golden import tile_alphabet_letter

    assert tile_alphabet_letter(0, 0) == "a"
    assert tile_alphabet_letter(1, 0) == "b"
    assert tile_alphabet_letter(0, 1) == "f"
    assert tile_alphabet_letter(4, 4) == "y"


@pytest.mark.unit
def test_render_packed_test_floor_matches_19x10_reference():
    from src.characters.editor_floor_test_tiles import (
        EDITOR_FLOOR_5X5_TILE_REFERENCE,
        render_packed_test_floor,
    )

    actual = render_packed_test_floor(5, use_orientation=False)
    assert actual == EDITOR_FLOOR_5X5_TILE_REFERENCE
    assert len(actual) == 10
    assert all(len(row) == 19 for row in actual)


@pytest.mark.unit
def test_alphabet_floor_draw_map_matches_reference():
    """5×5 alphabet patch via engine draw path → 19×10 canvas."""
    from src.characters.editor_floor_test_tiles import EDITOR_FLOOR_5X5_TILE_REFERENCE
    from src.engine.floor.draw_map import floor_packed_draw_map_from_cells
    from src.engine.layout.golden import (
        build_alphabet_floor_by_char,
        rasterize_packed_draw_map_to_canvas,
        tile_alphabet_letter,
    )

    by_char = build_alphabet_floor_by_char(0, 0, n_tiles=5)
    draw_map = floor_packed_draw_map_from_cells(
        by_char,
        0,
        0,
        n_tiles=5,
        glyph_for_tile=lambda tx, ty: tile_alphabet_letter(tx, ty, n_tiles=5),
    )
    assert len(draw_map) == 100

    canvas = rasterize_packed_draw_map_to_canvas(draw_map)
    assert canvas == EDITOR_FLOOR_5X5_TILE_REFERENCE
