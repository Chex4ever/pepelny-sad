"""Char/world cell → iso screen cell (2:1 projection)."""
from __future__ import annotations

from src.constants import ISO_STEP_X, ISO_STEP_Y


def char_cell_to_iso(
    cx: int,
    cy: int,
    *,
    ref_cx: int,
    ref_cy: int,
    step_x: int = ISO_STEP_X,
    step_y: int = ISO_STEP_Y,
) -> tuple[int, int]:
    """Game 2:1 iso offset (same formula as IsoProjector, origin at ref)."""
    dx, dy = cx - ref_cx, cy - ref_cy
    su = int(round((dx - dy) * step_x))
    sv = int(round((dx + dy) * step_y))
    return su, sv
