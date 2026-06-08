"""Alphabet test tiles: orientation quads + packed layout golden references."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_all_tile_quads_have_four_unique_letters():
    from src.characters.editor_floor_test_tiles import (
        tile_orientation_quad,
        validate_all_tile_quads,
        validate_tile_quad,
    )

    validate_all_tile_quads()
    for ty in range(5):
        for tx in range(5):
            validate_tile_quad(tile_orientation_quad(tx, ty))


@pytest.mark.unit
def test_wrong_stamp_orientation_detected():
    from src.characters.editor_floor_test_tiles import (
        is_tile_quad_canonical,
        tile_orientation_quad,
        validate_tile_quad,
    )

    quad = tile_orientation_quad(2, 2)
    validate_tile_quad(quad)
    rotated = (quad[1], quad[2], quad[3], quad[0])
    assert is_tile_quad_canonical(2, 2, rotated) is False
    assert is_tile_quad_canonical(2, 2, quad) is True


@pytest.mark.unit
def test_packed_5x5_display_tiles_match_alphabet_reference():
    from src.characters.editor_floor_test_tiles import (
        EDITOR_FLOOR_5X5_TILE_REFERENCE,
        assert_packed_test_floor_matches_reference,
        layout_sketch_row_widths,
    )

    assert_packed_test_floor_matches_reference(5, EDITOR_FLOOR_5X5_TILE_REFERENCE)
    widths = layout_sketch_row_widths()
    assert widths == (2, 6, 10, 14, 18, 18, 14, 10, 6, 2)


@pytest.mark.unit
def test_packed_2x2_orientation_tiles_match_reference():
    """Orientation: 2×2 tiles, 3×2 stamp, all 16 slots, one letter each."""
    from src.characters.editor_floor import packed_canvas_row_gap_count
    from src.characters.editor_floor_test_tiles import (
        EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE,
        compute_orientation_slot_view,
        render_orientation_packed_sketch,
        visible_orientation_glyphs,
    )

    glyphs = visible_orientation_glyphs(2)
    assert len(glyphs) == 16
    assert len(set(glyphs)) == 16
    assert len(compute_orientation_slot_view(n_tiles=2)) == 16

    actual = render_orientation_packed_sketch(2)
    assert actual == EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE
    assert packed_canvas_row_gap_count(actual) == 0


@pytest.mark.unit
def test_compute_tile_slot_view_geometry_for_5x5():
    from src.characters.editor_floor_test_tiles import TILE_SLOT_VIEW
    from src.engine.layout.golden import (
        EDITOR_FLOOR_5X5_TILE_CANVAS_VIEW,
        _packed_view_from_canvas,
    )

    assert len(TILE_SLOT_VIEW) == 100
    assert TILE_SLOT_VIEW == _packed_view_from_canvas(EDITOR_FLOOR_5X5_TILE_CANVAS_VIEW)


@pytest.mark.unit
def test_orientation_letters_differ_from_sketch_but_same_slots():
    from src.characters.editor_floor_test_tiles import (
        EDITOR_FLOOR_5X5_TILE_REFERENCE,
        render_packed_test_floor,
    )

    oriented = render_packed_test_floor(5, use_orientation=True)
    sketch = render_packed_test_floor(5, use_orientation=False)
    assert oriented != sketch
    assert oriented != EDITOR_FLOOR_5X5_TILE_REFERENCE
    for a, b in zip(oriented, sketch):
        assert (a == b) == (a.replace("_", "") == "" and b.replace("_", "") == "")


@pytest.mark.unit
def test_wrong_orientation_changes_oriented_raster():
    from src.characters.editor_floor_test_tiles import (
        render_packed_test_floor,
        tile_orientation_quad,
    )

    def rotated_quad(tx: int, ty: int):
        q = tile_orientation_quad(tx, ty)
        if tx == 2 and ty == 2:
            return (q[1], q[2], q[3], q[0])
        return q

    canonical = render_packed_test_floor(5, use_orientation=True)

    def custom_raster():
        from src.characters.editor_floor_test_tiles import TILE_SLOT_VIEW

        rows = [r for r, _c in TILE_SLOT_VIEW.values()]
        cols = [c for _r, c in TILE_SLOT_VIEW.values()]
        min_row, min_col = min(rows), min(cols)
        canvas_h = max(rows) - min_row + 1
        canvas_w = max(cols) - min_col + 1
        canvas = [list("_" * canvas_w) for _ in range(canvas_h)]
        for (tx, ty, slot), (row, col) in TILE_SLOT_VIEW.items():
            if tx == 2 and ty == 2:
                ch = rotated_quad(tx, ty)[slot]
            else:
                ch = tile_orientation_quad(tx, ty)[slot]
            canvas[row - min_row][col - min_col] = ch
        return tuple("".join(r) for r in canvas)

    assert custom_raster() != canonical


@pytest.mark.unit
def test_duplicate_quad_letters_rejected():
    from src.characters.editor_floor_test_tiles import validate_tile_quad

    with pytest.raises(ValueError, match="unique"):
        validate_tile_quad(("a", "a", "b", "c"))
