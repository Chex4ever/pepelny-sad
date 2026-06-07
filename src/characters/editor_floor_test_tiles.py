"""Alphabet test tiles: floor layout golden references.

One **floor tile** = **3×2** stamp ``@@_/_@@`` (four ``@`` cells).

**5×5 sketch** (``EDITOR_FLOOR_5X5_TILE_REFERENCE``): screen layout of the 1 m×1 m
patch. **One letter per tile**, that letter **4 times** (once per ``@``). Pairs like
``aa`` on a row = two ``@`` of the same tile adjacent on that row, not “one wide cell”.
Golden is **layout**, not glyph samples (in game every tile uses the same grass glyph).

**2×2 orientation sketch**: smaller patch, all 16 slots, one letter each — see
``render_orientation_packed_sketch`` (do not mix rules with the 5×5 sketch).
"""
from __future__ import annotations

from src.characters.editor_floor import packed_canvas_row_gap_count
from src.prototype.dia_scale.tessellation import ISO32_CELLS
from src.render.iso_character_view import EDITOR_FLOOR_TILES

STAMP_CELL_ORDER: tuple[tuple[int, int], ...] = tuple(sorted(ISO32_CELLS))

TILE_VIEW_CANVAS_W = 19
TILE_VIEW_CANVAS_H = 10

ORIENTATION_CANVAS_2X2_W = 7
ORIENTATION_CANVAS_2X2_H = 4

# Stamp slot draw order within one 3×2 tile (front row of @ first, then back row).
ORIENTATION_SLOT_DRAW_ORDER: tuple[int, ...] = (0, 1, 3, 2)

# User layout sketch — golden reference (5×5 packed, no row gaps).
EDITOR_FLOOR_5X5_TILE_REFERENCE: tuple[str, ...] = (
    "____kk_____________",
    "___ggkkpp__________",
    "__ddggllpptt_______",
    "_bbddhhllqqttww____",
    "aabbeehhmmqquuwwyy_",
    "_aacceeiimmrruuxxyy",
    "____ccffiinnrrvvxx_",
    "_______ffjjnnssvv__",
    "__________jjooss___",
    "_____________oo____",
)

# 2×2 tile patch, 3×2 stamp, all 16 @ slots, orientation quads (4 letters per tile).
EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE: tuple[str, ...] = (
    "_ef____",
    "abhgmn_",
    "_dcijpo",
    "____lk_",
)

# Canvas (row, col) for each slot in orientation sweep order (see compute_orientation_slot_view).
_ORIENTATION_CANVAS_CELLS_2X2: tuple[tuple[int, int], ...] = (
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (1, 0),
    (1, 1),
    (2, 1),
    (2, 2),
    (1, 4),
    (1, 5),
    (2, 5),
    (2, 6),
    (2, 3),
    (2, 4),
    (3, 4),
    (3, 5),
)

EDITOR_FLOOR_5X5_TILE_LAYOUT_SKETCH = EDITOR_FLOOR_5X5_TILE_REFERENCE

EDITOR_FLOOR_5X5_TILE_LAYOUT_ROW_WIDTHS: tuple[int, ...] = tuple(
    sum(1 for ch in row if ch != "_") for row in EDITOR_FLOOR_5X5_TILE_REFERENCE
)

# Sketch letter per visible stamp slot (5×5 display tiles — test fixture, not decoded).
TILE_SLOT_DISPLAY: dict[tuple[int, int, int], str] = {
    (0, 0, 2): "p",
    (0, 1, 0): "k",
    (0, 1, 1): "k",
    (0, 1, 2): "l",
    (0, 1, 3): "p",
    (0, 2, 0): "g",
    (0, 2, 1): "g",
    (0, 2, 2): "d",
    (0, 2, 3): "h",
    (0, 3, 0): "b",
    (0, 3, 1): "d",
    (0, 3, 2): "b",
    (0, 3, 3): "e",
    (0, 4, 1): "a",
    (0, 4, 2): "a",
    (1, 0, 2): "t",
    (1, 1, 2): "l",
    (1, 1, 3): "q",
    (1, 2, 2): "h",
    (1, 2, 3): "m",
    (1, 3, 2): "c",
    (1, 3, 3): "e",
    (1, 4, 3): "c",
    (2, 0, 2): "t",
    (2, 0, 3): "w",
    (2, 1, 2): "q",
    (2, 1, 3): "u",
    (2, 2, 2): "i",
    (2, 2, 3): "m",
    (2, 3, 2): "f",
    (2, 3, 3): "i",
    (3, 0, 2): "w",
    (3, 0, 3): "y",
    (3, 1, 2): "r",
    (3, 1, 3): "u",
    (3, 2, 2): "n",
    (3, 2, 3): "r",
    (3, 3, 2): "f",
    (3, 3, 3): "j",
    (4, 0, 2): "x",
    (4, 0, 3): "y",
    (4, 1, 1): "v",
    (4, 1, 2): "v",
    (4, 1, 3): "x",
    (4, 2, 1): "s",
    (4, 2, 2): "n",
    (4, 2, 3): "s",
    (4, 3, 2): "j",
    (4, 3, 3): "o",
    (4, 4, 3): "o",
}

# Iso (su, sv) anchors per row band — 5×5 packed canvas, feet at origin.
_ROW_PAIR_ISO_5X5: tuple[tuple[tuple[int, int], ...], ...] = (
    ((4, -4),),
    ((0, -4), (6, -3), (8, -2)),
    ((-2, -3), (2, -3), (4, -2), (6, -1), (8, 0)),
    ((-4, -4), (0, -2), (2, -1), (4, 0), (6, 1), (8, 2), (10, 3)),
    ((-6, -3), (-4, -2), (-2, -1), (0, 0), (2, 1), (4, 2), (6, 3), (8, 4), (10, 5)),
    ((-8, -2), (-4, 0), (-2, 1), (0, 2), (2, 3), (4, 4), (6, 5), (8, 6), (10, 7)),
    ((-6, 1), (-4, 2), (-2, 3), (0, 4), (2, 5), (4, 6), (6, 7)),
    ((-4, 4), (-2, 5), (0, 6), (2, 7), (6, 5)),
    ((-4, 6), (-2, 7), (2, 5)),
    ((-6, 7),),
)

def packed_canvas_dimensions(n_tiles: int) -> tuple[int, int]:
    """(width, height) of the display packed canvas (5×5 sketch only)."""
    if n_tiles == EDITOR_FLOOR_TILES:
        return TILE_VIEW_CANVAS_W, TILE_VIEW_CANVAS_H
    raise ValueError(f"display packed canvas is only defined for {EDITOR_FLOOR_TILES}×{EDITOR_FLOOR_TILES}")


def orientation_canvas_dimensions(n_tiles: int) -> tuple[int, int]:
    if n_tiles == 2:
        return ORIENTATION_CANVAS_2X2_W, ORIENTATION_CANVAS_2X2_H
    raise ValueError(f"orientation packed canvas is only defined for 2×2, got {n_tiles}×{n_tiles}")


def iter_orientation_tile_indices(n_tiles: int) -> tuple[tuple[int, int], ...]:
    """Tile sweep for orientation sketches: increasing ty, decreasing tx."""
    tiles = [(tx, ty) for ty in range(n_tiles) for tx in range(n_tiles)]
    return tuple(sorted(tiles, key=lambda t: (t[1], -t[0])))


def iter_floor_tile_view_pair_cols(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    canvas_h: int | None = None,
) -> tuple[tuple[int, int], ...]:
    """Diamond pair top-left columns: row index, col index (each pair is col, col+1)."""
    _h = canvas_h if canvas_h is not None else TILE_VIEW_CANVAS_H
    out = []
    for row in range(_h):
        if row <= 4:
            start = 4 - row
            n_pairs = 2 * row + 1
        else:
            start = 1 + 3 * (row - 5)
            n_pairs = 2 * (9 - row) + 1
        for k in range(n_pairs):
            out.append((row, start + 2 * k))
    return tuple(out)


def _pair_col_iso_anchor(row: int, col: int, *, n_tiles: int) -> tuple[int, int]:
    if row <= 4:
        start = 4 - row
    else:
        start = 1 + 3 * (row - 5)
    k = (col - start) // 2
    return _ROW_PAIR_ISO_5X5[row][k]


def _visible_stamp_slots_for_tile(tx: int, ty: int, n_tiles: int) -> frozenset[int]:
    """Front-facing @@ cells shown in the packed alphabet view."""
    if ty == n_tiles - 1:
        if tx == n_tiles - 1:
            return frozenset({3})
        if tx == 0:
            return frozenset({1, 2})
        if tx == 1:
            return frozenset({3})
        if n_tiles >= 4 and tx in (2, 3):
            return frozenset()
    if tx == 0 and ty == 0:
        return frozenset({2})
    if tx == 1 and ty == 0:
        return frozenset({2})
    if tx == 0:
        return frozenset({0, 1, 2, 3})
    if ty == 0:
        return frozenset({2, 3})
    if tx == n_tiles - 1:
        if ty == n_tiles - 2:
            return frozenset({2, 3})
        return frozenset({1, 2, 3})
    return frozenset({2, 3})


def compute_tile_slot_view(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    feet_cx: int = 0,
    feet_cy: int = 0,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Map visible stamp slots to packed canvas pair positions (diag + iso geometry)."""
    from src.characters.editor_floor import floor_screen_offset
    from src.prototype.dia_scale.tessellation import stamp_origin

    center = n_tiles // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    entries: list[dict[str, object]] = []
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            ox, oy = stamp_origin(tx, ty)
            for slot, (dx, dy) in enumerate(STAMP_CELL_ORDER):
                if slot not in _visible_stamp_slots_for_tile(tx, ty, n_tiles):
                    continue
                gx = ox - ref_ox + dx
                gy = oy - ref_oy + dy
                cx = feet_cx + gx
                cy = feet_cy + gy
                su, sv = floor_screen_offset(cx, cy, ref_cx=feet_cx, ref_cy=feet_cy)
                entries.append({"key": (tx, ty, slot), "su": su, "sv": sv})

    pair_cols = iter_floor_tile_view_pair_cols(n_tiles=n_tiles)
    if len(entries) != len(pair_cols):
        raise ValueError(
            f"expected {len(pair_cols)} visible stamp slots, got {len(entries)}"
        )

    unassigned = list(entries)
    out: dict[tuple[int, int, int], tuple[int, int]] = {}
    for row, col in pair_cols:
        tsu, tsv = _pair_col_iso_anchor(row, col, n_tiles=n_tiles)
        best_j = min(
            range(len(unassigned)),
            key=lambda j: (unassigned[j]["su"] - tsu) ** 2
            + (unassigned[j]["sv"] - tsv) ** 2,
        )
        entry = unassigned.pop(best_j)
        out[entry["key"]] = (row, col)
    return out


TILE_SLOT_VIEW: dict[tuple[int, int, int], tuple[int, int]] = compute_tile_slot_view(
    n_tiles=EDITOR_FLOOR_TILES
)


def compute_orientation_slot_view(
    *,
    n_tiles: int = 2,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Map every stamp slot to a single-char cell (orientation packed sketch)."""
    if n_tiles != 2:
        raise ValueError("orientation slot view is only defined for 2×2 tile patch")
    cells = _ORIENTATION_CANVAS_CELLS_2X2
    keys: list[tuple[int, int, int]] = []
    for tx, ty in iter_orientation_tile_indices(n_tiles):
        for slot in ORIENTATION_SLOT_DRAW_ORDER:
            keys.append((tx, ty, slot))
    if len(keys) != len(cells):
        raise ValueError(f"orientation canvas cell count mismatch: {len(keys)} vs {len(cells)}")
    return dict(zip(keys, cells))


def render_orientation_packed_sketch(
    n_tiles: int = 2,
    *,
    empty: str = "_",
) -> tuple[str, ...]:
    """Render orientation test floor: all @ slots, one orientation letter each."""
    canvas_w, canvas_h = orientation_canvas_dimensions(n_tiles)
    view = compute_orientation_slot_view(n_tiles=n_tiles)
    canvas = [[empty] * canvas_w for _ in range(canvas_h)]
    for (tx, ty, slot), (row, col) in view.items():
        ch = tile_orientation_quad(tx, ty, n_tiles=n_tiles)[slot]
        if 0 <= row < canvas_h and 0 <= col < canvas_w:
            canvas[row][col] = ch
    return tuple("".join(line) for line in canvas)


def tile_orientation_quad(
    tx: int,
    ty: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> tuple[str, str, str, str]:
    """Four unique lowercase letters identifying stamp slot order for (tx, ty)."""
    index = ty * n_tiles + tx
    return tuple(
        chr(ord("a") + ((index * 4 + slot) % 26))
        for slot in range(4)
    )


def slot_glyph(
    tx: int,
    ty: int,
    slot: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    use_orientation: bool = False,
) -> str | None:
    """Letter for a visible stamp slot (display sketch or orientation quad)."""
    key = (tx, ty, slot)
    if use_orientation:
        return tile_orientation_quad(tx, ty, n_tiles=n_tiles)[slot]
    if n_tiles != EDITOR_FLOOR_TILES:
        return tile_orientation_quad(tx, ty, n_tiles=n_tiles)[slot]
    return TILE_SLOT_DISPLAY.get(key)


def render_packed_test_floor(
    n_tiles: int = EDITOR_FLOOR_TILES,
    *,
    feet_cx: int = 0,
    feet_cy: int = 0,
    empty: str = "_",
    use_orientation: bool = False,
    slot_view: dict[tuple[int, int, int], tuple[int, int]] | None = None,
) -> tuple[str, ...]:
    """Render 5×5 display packed sketch (doubled letters, front-facing slots)."""
    if use_orientation:
        return render_orientation_packed_sketch(n_tiles=2, empty=empty)
    if n_tiles != EDITOR_FLOOR_TILES:
        raise ValueError(
            f"display packed sketch is only defined for {EDITOR_FLOOR_TILES}×{EDITOR_FLOOR_TILES}"
        )
    canvas_w, canvas_h = packed_canvas_dimensions(n_tiles)
    view = slot_view if slot_view is not None else compute_tile_slot_view(
        n_tiles=n_tiles, feet_cx=feet_cx, feet_cy=feet_cy
    )
    canvas = [[empty] * canvas_w for _ in range(canvas_h)]
    for (tx, ty, slot), (row, col) in view.items():
        ch = TILE_SLOT_DISPLAY.get((tx, ty, slot))
        if not ch:
            continue
        if 0 <= row < canvas_h and 0 <= col + 1 < canvas_w:
            canvas[row][col] = ch
            canvas[row][col + 1] = ch
    return tuple("".join(line) for line in canvas)


def assert_packed_test_floor_matches_reference(
    n_tiles: int,
    reference: tuple[str, ...],
    *,
    feet_cx: int = 0,
    feet_cy: int = 0,
    use_orientation: bool | None = None,
    require_no_row_gaps: bool = True,
) -> None:
    """Raise AssertionError if geometry render differs from golden sketch."""
    actual = render_packed_test_floor(
        n_tiles,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        use_orientation=use_orientation,
    )
    if actual != reference:
        diffs = [
            (i, a, b)
            for i, (a, b) in enumerate(zip(actual, reference))
            if a != b
        ]
        sample = diffs[:3]
        raise AssertionError(
            f"{n_tiles}×{n_tiles} packed floor differs on {len(diffs)} row(s), e.g. {sample}"
        )
    if require_no_row_gaps and packed_canvas_row_gap_count(actual) != 0:
        raise AssertionError("packed floor has row gaps between glyph pairs")


def validate_tile_quad(quad: tuple[str, ...]) -> None:
    if len(quad) != 4:
        raise ValueError(f"tile quad must have 4 letters, got {len(quad)}")
    if len(set(quad)) != 4:
        raise ValueError(f"tile quad letters must be unique, got {quad!r}")
    for ch in quad:
        if len(ch) != 1 or not ch.isalpha():
            raise ValueError(f"tile quad must be single letters, got {quad!r}")


def validate_all_tile_quads(*, n_tiles: int = EDITOR_FLOOR_TILES) -> None:
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            validate_tile_quad(tile_orientation_quad(tx, ty, n_tiles=n_tiles))


def is_tile_quad_canonical(
    tx: int,
    ty: int,
    quad: tuple[str, ...],
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> bool:
    validate_tile_quad(quad)
    return quad == tile_orientation_quad(tx, ty, n_tiles=n_tiles)


def rasterize_test_tile_view(
    *,
    canvas_w: int = TILE_VIEW_CANVAS_W,
    canvas_h: int = TILE_VIEW_CANVAS_H,
    empty: str = "_",
    use_orientation: bool = False,
    slot_view: dict[tuple[int, int, int], tuple[int, int]] | None = None,
) -> tuple[str, ...]:
    """Rasterize 5×5 alphabet floor (legacy alias for ``render_packed_test_floor``)."""
    _ = canvas_w, canvas_h, empty
    return render_packed_test_floor(
        EDITOR_FLOOR_TILES,
        use_orientation=use_orientation,
        slot_view=slot_view,
    )


def assert_test_tile_view_matches_reference(
    *,
    reference: tuple[str, ...] = EDITOR_FLOOR_5X5_TILE_REFERENCE,
) -> None:
    assert_packed_test_floor_matches_reference(
        EDITOR_FLOOR_TILES,
        reference,
        use_orientation=False,
    )


def layout_sketch_row_widths(
    sketch: tuple[str, ...] = EDITOR_FLOOR_5X5_TILE_LAYOUT_SKETCH,
) -> tuple[int, ...]:
    return tuple(sum(1 for ch in row if ch != "_") for row in sketch)


def visible_orientation_glyphs(n_tiles: int = 2) -> tuple[str, ...]:
    """Orientation letters placed on the 2×2 packed sketch (16 unique)."""
    view = compute_orientation_slot_view(n_tiles=n_tiles)
    return tuple(
        tile_orientation_quad(tx, ty, n_tiles=n_tiles)[slot]
        for tx, ty, slot in view
    )
