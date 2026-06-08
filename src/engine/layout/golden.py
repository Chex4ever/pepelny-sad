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

from src.engine.config import FLOOR_LAYOUT_TILES as EDITOR_FLOOR_TILES
from src.engine.floor.validate import packed_canvas_row_gap_count
from src.prototype.dia_scale.tessellation import ISO32_CELLS

STAMP_CELL_ORDER: tuple[tuple[int, int], ...] = tuple(sorted(ISO32_CELLS))

TILE_VIEW_CANVAS_W = 19
TILE_VIEW_CANVAS_H = 10

ORIENTATION_CANVAS_2X2_W = 7
ORIENTATION_CANVAS_2X2_H = 4

# Stamp slot draw order within one 3×2 tile (front row of @ first, then back row).
ORIENTATION_SLOT_DRAW_ORDER: tuple[int, ...] = (0, 1, 3, 2)

# User layout sketch — golden reference (5×5 packed, 19×10 canvas, no row gaps).
# Tile (tx, ty) → letter ``a`` + ty * n + tx (four identical glyphs per stamp).
EDITOR_FLOOR_5X5_TILE_REFERENCE: tuple[str, ...] = (
    "____uu_____________",
    "___ppuuvv__________",
    "__kkppqqvvww_______",
    "_ffkkllqqrrwwxx____",
    "aaffggllmmrrssxxyy_",
    "_aabbgghhmmnnssttyy",
    "____bbcchhiinnoott_",
    "_______ccddiijjoo__",
    "__________ddeejj___",
    "_____________ee____",
)

_STAMP_CANVAS_OFFSETS: tuple[tuple[int, int], ...] = ((0, 0), (0, 1), (1, 1), (1, 2))

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

# Feet anchor on the 19×10 packed layout canvas (center tile visible band).
PACKED_LAYOUT_FEET_COL = 9
PACKED_LAYOUT_FEET_ROW = 5

def packed_layout_silhouette(
    reference: tuple[str, ...] = EDITOR_FLOOR_5X5_TILE_REFERENCE,
) -> frozenset[tuple[int, int]]:
    """Every (col, row) glyph cell in the layout golden (editor screen diamond)."""
    cells: set[tuple[int, int]] = set()
    for row, line in enumerate(reference):
        for col, ch in enumerate(line):
            if ch != "_":
                cells.add((col, row))
    return frozenset(cells)


def packed_layout_screen_offset(col: int, row: int) -> tuple[int, int]:
    """Screen offset from feet on the packed layout grid (one cell per col)."""
    from src.engine.projection.packed import layout_cell_to_screen

    return layout_cell_to_screen(col, row)

def tile_alphabet_letter(
    tx: int,
    ty: int,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> str:
    """Test tile label: ``(0,0)`` → ``a``, ``(1,0)`` → ``b``, ``(0,1)`` → ``f``, … ``(4,4)`` → ``y``."""
    index = ty * n_tiles + tx
    return chr(ord("a") + index)


def _decode_tile_canvas_view_from_reference(
    reference: tuple[str, ...],
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """``(tx, ty, slot)`` → absolute canvas ``(row, col)`` on 19×10."""
    from collections import defaultdict

    groups: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for row, line in enumerate(reference):
        for col, ch in enumerate(line):
            if ch == "_":
                continue
            index = ord(ch) - ord("a")
            tx, ty = index % n_tiles, index // n_tiles
            groups[(tx, ty)].append((row, col))

    out: dict[tuple[int, int, int], tuple[int, int]] = {}
    for (tx, ty), positions in groups.items():
        pos_set = set(positions)
        anchor: tuple[int, int] | None = None
        for pos in positions:
            if all((pos[0] + dr, pos[1] + dc) in pos_set for dr, dc in _STAMP_CANVAS_OFFSETS):
                anchor = pos
                break
        if anchor is None:
            raise ValueError(f"stamp anchor not found for tile ({tx}, {ty}) in reference")
        for slot, (dr, dc) in enumerate(_STAMP_CANVAS_OFFSETS):
            out[(tx, ty, slot)] = (anchor[0] + dr, anchor[1] + dc)
    return out


def _packed_view_from_canvas(
    canvas_view: dict[tuple[int, int, int], tuple[int, int]],
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Canvas ``(row, col)`` → packed ``(row, col)`` relative to feet on 19×10."""
    fr, fc = PACKED_LAYOUT_FEET_ROW, PACKED_LAYOUT_FEET_COL
    return {
        key: (row - fr, col - fc)
        for key, (row, col) in canvas_view.items()
    }


EDITOR_FLOOR_5X5_TILE_CANVAS_VIEW: dict[tuple[int, int, int], tuple[int, int]] = (
    _decode_tile_canvas_view_from_reference(EDITOR_FLOOR_5X5_TILE_REFERENCE)
)

TILE_SLOT_DISPLAY: dict[tuple[int, int, int], str] = {
    (tx, ty, slot): tile_alphabet_letter(tx, ty)
    for ty in range(EDITOR_FLOOR_TILES)
    for tx in range(EDITOR_FLOOR_TILES)
    for slot in range(4)
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
    pair_scale: int = 1,
) -> tuple[tuple[int, int], ...]:
    """Diamond pair top-left columns: row index, col index (each pair is col, col+1).

    Canvas height ``2 × n_tiles``; row widths grow to the center then shrink — diag diamond
    per ``docs/ISO_LAYOUT.md`` (not horizontal iso bands).

    ``pair_scale=2`` doubles pair slots per row (all four @@ stamp cells per tile).
    """
    _h = canvas_h if canvas_h is not None else 2 * n_tiles
    mid = n_tiles - 1
    peak = 2 * n_tiles - 1
    out: list[tuple[int, int]] = []
    for row in range(_h):
        if row <= mid:
            start = mid - row
            n_pairs = (2 * row + 1) * pair_scale
        else:
            start = 1 + 3 * (row - n_tiles)
            n_pairs = (2 * (peak - row) + 1) * pair_scale
        for k in range(n_pairs):
            out.append((row, start + 2 * k))
    return tuple(out)


def _pair_col_iso_anchor(row: int, col: int, *, n_tiles: int) -> tuple[int, int]:
    """Iso (su, sv) target for greedy slot → diamond pair assignment."""
    mid = n_tiles - 1
    if row <= mid:
        start = mid - row
        n_pairs = 2 * row + 1
    else:
        start = 1 + 3 * (row - n_tiles)
        n_pairs = 2 * (2 * n_tiles - 1 - row) + 1
    k = max(0, min(n_pairs - 1, (col - start) // 2))

    if n_tiles == EDITOR_FLOOR_TILES and row < len(_ROW_PAIR_ISO_5X5):
        return _ROW_PAIR_ISO_5X5[row][k]

    ref_h = len(_ROW_PAIR_ISO_5X5)
    ref_row = min(
        ref_h - 1,
        max(0, round(row * (ref_h - 1) / max(1, 2 * n_tiles - 1))),
    )
    ref_anchors = _ROW_PAIR_ISO_5X5[ref_row]
    ref_n = len(ref_anchors)
    if n_pairs <= 1:
        ref_k = 0
    else:
        ref_k = int(round(k * (ref_n - 1) / (n_pairs - 1)))
    ref_k = max(0, min(ref_n - 1, ref_k))
    su, sv = ref_anchors[ref_k]
    scale = (n_tiles - 1) / 4.0
    return int(round(su * scale)), int(round(sv * scale))


def _collect_stamp_slot_entries(
    n_tiles: int,
    feet_cx: int,
    feet_cy: int,
    *,
    all_slots: bool,
) -> list[dict[str, object]]:
    from src.engine.projection.iso import char_cell_to_iso
    from src.prototype.dia_scale.tessellation import stamp_origin

    center = n_tiles // 2
    ref_ox, ref_oy = stamp_origin(center, center)
    entries: list[dict[str, object]] = []
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            ox, oy = stamp_origin(tx, ty)
            for slot, (dx, dy) in enumerate(STAMP_CELL_ORDER):
                if not all_slots and slot not in _visible_stamp_slots_for_tile(tx, ty, n_tiles):
                    continue
                gx = ox - ref_ox + dx
                gy = oy - ref_oy + dy
                cx = feet_cx + gx
                cy = feet_cy + gy
                su, sv = char_cell_to_iso(cx, cy, ref_cx=feet_cx, ref_cy=feet_cy)
                entries.append({"key": (tx, ty, slot), "su": su, "sv": sv})
    return entries


def _assign_entries_to_diamond(
    entries: list[dict[str, object]],
    pair_cols: tuple[tuple[int, int], ...],
    *,
    n_tiles: int,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    if len(entries) != len(pair_cols):
        raise ValueError(
            f"diamond pair grid size {len(pair_cols)} != stamp slot count {len(entries)} "
            f"for {n_tiles}×{n_tiles} patch"
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
        out[entry["key"]] = (row, col)  # type: ignore[index]
    return out


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


def _fit_pair_grid_to_entries(
    pair_cols: tuple[tuple[int, int], ...],
    n_entries: int,
    *,
    n_tiles: int,
) -> tuple[tuple[int, int], ...]:
    """Grow or shrink diamond pair list to match stamp-slot count (per-tile layout)."""
    cols = list(pair_cols)
    if len(cols) == n_entries:
        return tuple(cols)
    if len(cols) > n_entries:
        return tuple(cols[:n_entries])

    mid = n_tiles - 1
    peak = 2 * n_tiles - 1
    widest = 2 * mid + 1
    row = mid
    while len(cols) < n_entries:
        start = mid - row if row <= mid else 1 + 3 * (row - n_tiles)
        n_pairs = (2 * row + 1) if row <= mid else (2 * (peak - row) + 1)
        for k in range(n_pairs):
            cols.append((row, start + 2 * k))
            if len(cols) >= n_entries:
                break
        row += 1
        if row > peak + widest:
            row = 0
    return tuple(cols[:n_entries])


def compute_tile_slot_view(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    feet_cx: int = 0,
    feet_cy: int = 0,
    all_slots: bool = False,
    pair_scale: int = 1,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Map stamp slots to packed diamond — per tile, iso-matched (golden when n=5 sketch)."""
    entries = _collect_stamp_slot_entries(
        n_tiles, feet_cx, feet_cy, all_slots=all_slots,
    )
    pair_cols = iter_floor_tile_view_pair_cols(n_tiles=n_tiles, pair_scale=pair_scale)
    pair_cols = _fit_pair_grid_to_entries(pair_cols, len(entries), n_tiles=n_tiles)
    return _assign_entries_to_diamond(entries, pair_cols, n_tiles=n_tiles)


def compute_tile_slot_view_patch(
    *,
    n_tiles: int,
    feet_cx: int = 0,
    feet_cy: int = 0,
    cam_tx: int = 0,
    cam_ty: int = 0,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Full patch: 5×5 uses 19×10 golden canvas; larger patches use screen-row stamps."""
    _ = feet_cx, feet_cy
    if n_tiles == EDITOR_FLOOR_TILES:
        _ = cam_tx, cam_ty
        return dict(_packed_view_from_canvas(EDITOR_FLOOR_5X5_TILE_CANVAS_VIEW))
    from src.engine.layout.screen_slots import compute_tile_slot_view_screen

    return compute_tile_slot_view_screen(
        n_tiles=n_tiles, cam_tx=cam_tx, cam_ty=cam_ty,
    )


def resolve_tile_slot_view(
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
    feet_cx: int = 0,
    feet_cy: int = 0,
    cam_tx: int = 0,
    cam_ty: int = 0,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Packed slot view — same tile formula for character and level editors."""
    _ = feet_cx, feet_cy
    return compute_tile_slot_view_patch(
        n_tiles=n_tiles,
        feet_cx=feet_cx,
        feet_cy=feet_cy,
        cam_tx=cam_tx,
        cam_ty=cam_ty,
    )


TILE_SLOT_VIEW: dict[tuple[int, int, int], tuple[int, int]] = resolve_tile_slot_view(
    n_tiles=EDITOR_FLOOR_TILES,
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
    """Render 5×5 display packed sketch (one letter per stamp slot)."""
    if use_orientation:
        return render_orientation_packed_sketch(n_tiles=2, empty=empty)
    if n_tiles != EDITOR_FLOOR_TILES:
        raise ValueError(
            f"display packed sketch is only defined for {EDITOR_FLOOR_TILES}×{EDITOR_FLOOR_TILES}"
        )
    packed_view = slot_view if slot_view is not None else resolve_tile_slot_view(
        n_tiles=n_tiles, feet_cx=feet_cx, feet_cy=feet_cy,
    )
    if not packed_view:
        return (empty,)
    canvas_w, canvas_h = packed_canvas_dimensions(n_tiles)
    fr, fc = PACKED_LAYOUT_FEET_ROW, PACKED_LAYOUT_FEET_COL
    canvas = [[empty] * canvas_w for _ in range(canvas_h)]
    for (tx, ty, slot), (row, col) in packed_view.items():
        ch = slot_glyph(tx, ty, slot, n_tiles=n_tiles, use_orientation=False)
        if not ch:
            continue
        r, c = row + fr, col + fc
        if 0 <= r < canvas_h and 0 <= c < canvas_w:
            canvas[r][c] = ch
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


def build_alphabet_floor_by_char(
    feet_cx: int = 0,
    feet_cy: int = 0,
    *,
    n_tiles: int = EDITOR_FLOOR_TILES,
) -> dict[tuple[int, int], "FloorGlyphCell"]:
    """5×5 floor patch: each tile's four stamp cells use the same alphabet letter."""
    from src.engine.floor.patch import floor_stamp_tile_owners
    from src.engine.floor.types import (
        FLOOR_TILE_A_BG,
        FLOOR_TILE_A_FG,
        FLOOR_TILE_B_BG,
        FLOOR_TILE_B_FG,
        FloorGlyphCell,
    )

    owners = floor_stamp_tile_owners(feet_cx, feet_cy, n_tiles=n_tiles)
    cells: dict[tuple[int, int], FloorGlyphCell] = {}
    for (cx, cy), (tx, ty) in owners.items():
        even = (tx + ty) % 2 == 0
        ch = tile_alphabet_letter(tx, ty, n_tiles=n_tiles)
        fg = FLOOR_TILE_A_FG if even else FLOOR_TILE_B_FG
        bg = FLOOR_TILE_A_BG if even else FLOOR_TILE_B_BG
        cells[(cx, cy)] = FloorGlyphCell(
            cx, cy, ch, fg, bg, solid=True, tile_tx=tx, tile_ty=ty,
        )
    return cells


def rasterize_packed_draw_map_to_canvas(
    draw_map: dict[tuple[int, int], "FloorGlyphCell"],
    *,
    canvas_w: int = TILE_VIEW_CANVAS_W,
    canvas_h: int = TILE_VIEW_CANVAS_H,
    empty: str = "_",
) -> tuple[str, ...]:
    """Rasterize packed ``(col, row)`` draw map onto the fixed 19×10 layout canvas."""
    fr, fc = PACKED_LAYOUT_FEET_ROW, PACKED_LAYOUT_FEET_COL
    canvas = [[empty] * canvas_w for _ in range(canvas_h)]
    for (col, row), cell in draw_map.items():
        r, c = row + fr, col + fc
        if 0 <= r < canvas_h and 0 <= c < canvas_w:
            canvas[r][c] = cell.ch
    return tuple("".join(line) for line in canvas)


def visible_orientation_glyphs(n_tiles: int = 2) -> tuple[str, ...]:
    """Orientation letters placed on the 2×2 packed sketch (16 unique)."""
    view = compute_orientation_slot_view(n_tiles=n_tiles)
    return tuple(
        tile_orientation_quad(tx, ty, n_tiles=n_tiles)[slot]
        for tx, ty, slot in view
    )
