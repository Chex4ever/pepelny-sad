"""Compute screen origin to center projected content."""
from __future__ import annotations


def center_origin(
    *,
    panel_w: int,
    panel_h: int,
    margin: int,
    title_h: int,
    bottom_h: int,
    cell_w: int,
    cell_h: int,
    min_u: int,
    max_u: int,
    min_v: int,
    max_v: int,
) -> tuple[int, int]:
    avail_w = panel_w - margin * 2
    avail_h = panel_h - margin * 2 - title_h - bottom_h
    span_u = max(1, max_u - min_u + 1)
    span_v = max(1, max_v - min_v + 1)
    ox = margin + (avail_w - span_u * cell_w) // 2 - min_u * cell_w
    oy = margin + title_h + (avail_h - span_v * cell_h) // 2 - min_v * cell_h
    return ox, oy
