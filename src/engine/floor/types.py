"""Floor glyph and patch types."""
from __future__ import annotations

from dataclasses import dataclass

from src.prototype.dia_scale.constants import COLOR_FLOOR_ALT_FG, COLOR_FLOOR_FG

FLOOR_TILE_A_BG = (32, 48, 30)
FLOOR_TILE_B_BG = (48, 38, 28)
FLOOR_TILE_A_FG = COLOR_FLOOR_FG
FLOOR_TILE_B_FG = (145, 120, 85)


@dataclass(frozen=True)
class FloorGlyphCell:
    cx: int
    cy: int
    ch: str
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]
    solid: bool = True
    tile_tx: int = 0
    tile_ty: int = 0
