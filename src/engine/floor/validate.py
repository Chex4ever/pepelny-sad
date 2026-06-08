"""Row/canvas gap helpers for packed floor validation."""
from __future__ import annotations


def floor_row_gap_count(view: frozenset[tuple[int, int]] | set[tuple[int, int]]) -> int:
    if not view:
        return 0
    by_row: dict[int, list[int]] = {}
    for u, v in view:
        by_row.setdefault(v, []).append(u)
    gaps = 0
    for us in by_row.values():
        us.sort()
        for left, right in zip(us, us[1:]):
            gaps += right - left - 1
    return gaps


def floor_row_span_holes(
    view: frozenset[tuple[int, int]] | set[tuple[int, int]],
) -> list[tuple[int, int, int]]:
    if not view:
        return []
    by_row: dict[int, list[int]] = {}
    for u, v in view:
        by_row.setdefault(v, []).append(u)
    out: list[tuple[int, int, int]] = []
    for v, us in by_row.items():
        us.sort()
        span = us[-1] - us[0] + 1
        if len(us) != span:
            out.append((v, span - len(us), span))
    return out


def packed_canvas_row_gap_count(rows: tuple[str, ...]) -> int:
    gaps = 0
    for row in rows:
        cols = [i for i, ch in enumerate(row) if ch != "_"]
        if len(cols) < 2:
            continue
        for left, right in zip(cols, cols[1:]):
            gaps += right - left - 1
    return gaps
