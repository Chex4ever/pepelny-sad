"""Packed layout grid → screen cell offsets."""
from __future__ import annotations

from dataclasses import dataclass

from src.engine.layout.golden import (
    PACKED_LAYOUT_FEET_COL,
    PACKED_LAYOUT_FEET_ROW,
)


@dataclass(frozen=True)
class LayoutFeet:
    col: int = PACKED_LAYOUT_FEET_COL
    row: int = PACKED_LAYOUT_FEET_ROW


def layout_cell_to_screen(
    col: int,
    row: int,
    *,
    feet: LayoutFeet | None = None,
) -> tuple[int, int]:
    """Screen offset from feet on the packed layout grid."""
    fc = PACKED_LAYOUT_FEET_COL if feet is None else feet.col
    fr = PACKED_LAYOUT_FEET_ROW if feet is None else feet.row
    return (col - fc, row - fr)
