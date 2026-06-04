"""Effective map viewport size (chars in classic, tiles in iso)."""
from __future__ import annotations

from src.constants import MAP_VIEW_H, MAP_VIEW_TILES_H, MAP_VIEW_TILES_W, MAP_VIEW_W
from src.render.render_mode import is_iso


def map_view_w() -> int:
    return MAP_VIEW_TILES_W if is_iso() else MAP_VIEW_W


def map_view_h() -> int:
    return MAP_VIEW_TILES_H if is_iso() else MAP_VIEW_H


def map_pan_cell_w() -> int:
    from src.constants import CELL_W, ISO_TILE_PIXEL_W

    return ISO_TILE_PIXEL_W if is_iso() else CELL_W


def map_pan_cell_h() -> int:
    from src.constants import CELL_H, ISO_TILE_PIXEL_H

    return ISO_TILE_PIXEL_H if is_iso() else CELL_H
