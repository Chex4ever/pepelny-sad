"""ASCII floor screen layout — stamp slots on screen rows (docs/ISO_LAYOUT.md).

Stamp (user 1..4, left→right, top→bottom)::

    1 2 _
    _ 3 4

``screen_row_tile_slot(sr, sc)`` defines the scan-line rule (4-row cycle).
Each tile's four slots form one 3×2 stamp on screen: find anchor from the rule,
then place slots 1–2 on row R and 3–4 on row R+1.  Camera pan subtracts the
anchor screen cell of ``(cam_tx, cam_ty)`` slot **1**.
"""
from __future__ import annotations

from collections import defaultdict

from src.engine.layout.golden import STAMP_CELL_ORDER
from src.prototype.dia_scale.tessellation import stamp_origin

# User reference for the first four screen rows (tile x, tile y, user slot 1..4).
_REFERENCE_ROWS: tuple[tuple[tuple[int, int, int], ...], ...] = (
    (
        (0, 0, 1), (0, 0, 2), (0, 1, 3), (0, 1, 4),
        (1, 1, 1), (1, 1, 2), (1, 2, 3), (1, 2, 4),
        (2, 2, 1), (2, 2, 2), (2, 3, 3), (2, 3, 4),
    ),
    (
        (0, -1, 2), (0, 0, 3), (0, 0, 4), (1, 0, 1), (1, 0, 2),
        (1, 1, 3), (1, 1, 4), (2, 1, 1), (2, 1, 2), (2, 2, 3), (2, 2, 4),
        (3, 2, 1),
    ),
    (
        (0, -1, 3), (0, -1, 4), (1, -1, 1), (1, -1, 2), (1, 0, 3), (1, 0, 4),
        (2, 0, 1), (2, 0, 2), (2, 1, 3), (2, 1, 4), (3, 1, 1), (3, 1, 2),
    ),
    (
        (0, -2, 4), (1, -2, 1), (1, -2, 2), (1, -1, 3), (1, -1, 4),
        (2, -1, 1), (2, -1, 2), (2, 0, 3), (2, 0, 4), (3, 0, 1), (3, 0, 2),
        (3, 1, 3),
    ),
)

# Screen offsets for slots 0..3 when slot 0 anchor is at (sr, sc).
_STAMP_FROM_SLOT0: tuple[tuple[int, int], ...] = ((0, 0), (0, 1), (1, 1), (1, 2))
# When only slots 2,3 are found on one row (north-edge tiles), derive slot 0 anchor.
_STAMP_FROM_SLOT2: tuple[tuple[int, int], ...] = ((-1, -1), (-1, 0), (0, 0), (0, 1))


def screen_row_tile_slot(sr: int, sc: int) -> tuple[int, int, int]:
    """Screen (row, col) → tessellation tile ``(tx, ty)`` and slot ``0..3``."""
    band = sr // 4
    ty_shift = 4 * band
    r = sr % 4
    phase = (sc + sr) % 4
    slot = phase

    if r == 0:
        i = sc // 4
        if phase < 2:
            tx, ty = i, i
        else:
            tx, ty = i, i + 1
    elif r == 1:
        if sc == 0:
            return 0, -1 + ty_shift, 1
        i = (sc - 1) // 4
        if phase < 2:
            tx, ty = i + 1, i
        else:
            tx, ty = i, i
    elif r == 2:
        if sc == 0:
            return 0, -1 + ty_shift, 2
        if sc == 1:
            return 0, -1 + ty_shift, 3
        i = (sc - 2) // 4 + 1
        if phase < 2:
            tx, ty = i, i - 2
        else:
            tx, ty = i, i - 1
    else:
        if sc == 0:
            return 0, -2 + ty_shift, 3
        i = (sc - 1) // 4 + 1
        if phase < 2:
            tx, ty = i, i - 3
        else:
            tx, ty = i, i - 2

    return tx, ty + ty_shift, slot


def _find_stamp_anchor_fwd(tx: int, ty: int, n_tiles: int) -> tuple[int, int] | None:
    """Row/col of slot 0 where slot 1 is at (sr, sc+1) on the same screen row."""
    sc_max = 4 * n_tiles
    for sr in range(-n_tiles, 4 * n_tiles):
        for sc in range(sc_max - 1):
            if screen_row_tile_slot(sr, sc) != (tx, ty, 0):
                continue
            if screen_row_tile_slot(sr, sc + 1) == (tx, ty, 1):
                return sr, sc
    return None


def _find_stamp_anchor_back(tx: int, ty: int, n_tiles: int) -> tuple[int, int] | None:
    """Row/col of slot 2 where slot 3 is at (sr, sc+1) — north-edge tiles."""
    sc_max = 4 * n_tiles
    for sr in range(-n_tiles, 4 * n_tiles):
        for sc in range(sc_max - 1):
            if screen_row_tile_slot(sr, sc) != (tx, ty, 2):
                continue
            if screen_row_tile_slot(sr, sc + 1) == (tx, ty, 3):
                return sr, sc
    return None


def _collect_scan_hits(n_tiles: int) -> dict[tuple[int, int, int], list[tuple[int, int]]]:
    hits: dict[tuple[int, int, int], list[tuple[int, int]]] = defaultdict(list)
    sc_max = 4 * n_tiles
    for sr in range(-n_tiles, 4 * n_tiles):
        for sc in range(sc_max):
            tx, ty, slot = screen_row_tile_slot(sr, sc)
            if 0 <= tx < n_tiles and 0 <= ty < n_tiles:
                hits[(tx, ty, slot)].append((sr, sc))
    return hits


_STAMP_LAYOUT_CACHE: dict[int, dict[tuple[int, int, int], tuple[int, int]]] = {}


def clear_stamp_layout_cache() -> None:
    """Test helper — drop cached stamp layouts."""
    _STAMP_LAYOUT_CACHE.clear()


def _build_stamp_layout(
    n_tiles: int,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """Place every stamp as one 3×2 block; no split slots across bands."""
    cached = _STAMP_LAYOUT_CACHE.get(n_tiles)
    if cached is not None:
        return cached
    layout: dict[tuple[int, int, int], tuple[int, int]] = {}
    occupied: set[tuple[int, int]] = set()

    def _place_stamp(tx: int, ty: int, sr0: int, sc0: int, offsets: tuple[tuple[int, int], ...]) -> bool:
        pos = {(tx, ty, slot): (sr0 + dr, sc0 + dc) for slot, (dr, dc) in enumerate(offsets)}
        if any(p in occupied for p in pos.values()):
            return False
        layout.update(pos)
        occupied.update(pos.values())
        return True

    for ty in range(n_tiles):
        for tx in range(n_tiles):
            anchor = _find_stamp_anchor_fwd(tx, ty, n_tiles)
            if anchor is not None:
                _place_stamp(tx, ty, anchor[0], anchor[1], _STAMP_FROM_SLOT0)

    for ty in range(n_tiles):
        for tx in range(n_tiles):
            if (tx, ty, 0) in layout:
                continue
            anchor = _find_stamp_anchor_back(tx, ty, n_tiles)
            if anchor is not None:
                _place_stamp(tx, ty, anchor[0], anchor[1], _STAMP_FROM_SLOT2)

    hits = _collect_scan_hits(n_tiles)
    for ty in range(n_tiles):
        for tx in range(n_tiles):
            for slot in range(4):
                key = (tx, ty, slot)
                if key in layout:
                    continue
                for sr, sc in sorted(hits.get(key, [])):
                    if (sr, sc) not in occupied:
                        layout[key] = (sr, sc)
                        occupied.add((sr, sc))
                        break

    _STAMP_LAYOUT_CACHE[n_tiles] = layout
    return layout


def build_tile_slot_screen_map(
    n_tiles: int,
    *,
    cam_tx: int = 0,
    cam_ty: int = 0,
    sr_min: int | None = None,
    sr_max: int | None = None,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    """``(tx, ty, slot)`` → packed ``(row, col)``; anchor tile slot 1 at ``(0, 0)``."""
    _ = sr_min, sr_max
    raw = _build_stamp_layout(n_tiles)
    ar, ac = raw.get((cam_tx, cam_ty, 0), (0, 0))
    return {
        key: (sr - ar, sc - ac)
        for key, (sr, sc) in raw.items()
    }


def packed_pick_map_from_slot_view(
    slot_view: dict[tuple[int, int, int], tuple[int, int]],
) -> dict[tuple[int, int], tuple[int, int]]:
    """Packed ``(col, row)`` → layout tile ``(tx, ty)`` from a slot view."""
    return {(col, row): (tx, ty) for (tx, ty, _slot), (row, col) in slot_view.items()}


def build_packed_tile_pick_map(
    n_tiles: int,
    *,
    cam_tx: int = 0,
    cam_ty: int = 0,
    slot_view: dict[tuple[int, int, int], tuple[int, int]] | None = None,
) -> dict[tuple[int, int], tuple[int, int]]:
    """Packed ``(col, row)`` → layout tile ``(tx, ty)`` for editor picking."""
    if slot_view is None:
        from src.engine.layout.golden import resolve_tile_slot_view

        slot_view = resolve_tile_slot_view(n_tiles=n_tiles, cam_tx=cam_tx, cam_ty=cam_ty)
    return packed_pick_map_from_slot_view(slot_view)


def tile_slot_packed_pos(
    tx: int,
    ty: int,
    slot: int,
    *,
    cam_tx: int = 0,
    cam_ty: int = 0,
    n_tiles: int | None = None,
) -> tuple[int, int]:
    """Packed layout ``(row, col)`` for one stamp slot."""
    from src.engine.layout.golden import resolve_tile_slot_view

    side = n_tiles if n_tiles is not None else max(tx, ty, cam_tx, cam_ty) + 1
    view = resolve_tile_slot_view(n_tiles=side, cam_tx=cam_tx, cam_ty=cam_ty)
    return view[(tx, ty, slot)]


def compute_tile_slot_view_screen(
    *,
    n_tiles: int,
    cam_tx: int = 0,
    cam_ty: int = 0,
) -> dict[tuple[int, int, int], tuple[int, int]]:
    return build_tile_slot_screen_map(n_tiles, cam_tx=cam_tx, cam_ty=cam_ty)
