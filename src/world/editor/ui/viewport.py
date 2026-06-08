"""Level editor viewport — diag 3×2 stamp packed layout (docs/ISO_LAYOUT.md)."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.engine.config import FLOOR_LAYOUT_TILES
from src.engine.floor.draw_map import floor_packed_draw_map_from_cells
from src.engine.floor.types import FloorGlyphCell
from src.engine.floor.world_patch import build_floor_patch_from_world, world_column_getter
from src.engine.projection.packed import layout_cell_to_screen
from src.engine.viewport.floor import draw_packed_floor_map
from src.prototype.dia_scale.display_scale import PRESET_NORMAL
from src.world.editor.editable_world import EditableWorld


@dataclass
class DiagViewportLayout:
    """Screen layout for picking after draw."""

    ox: int
    oy: int
    cell_w: int
    cell_h: int
    draw_map: dict[tuple[int, int], FloorGlyphCell]
    packed_tile_at: dict[tuple[int, int], tuple[int, int]]
    wx0: int
    wy0: int
    n_tiles: int


def _patch_extent(world: EditableWorld) -> tuple[int, int, int]:
    """Full editable patch: (n_tiles, wx0, wy0)."""
    b = world.bounds
    return b.width, b.wx0, b.wy0


def build_world_packed_draw_map(
    world: EditableWorld,
    *,
    n_tiles: int | None = None,
    slot_view: dict[tuple[int, int, int], tuple[int, int]] | None = None,
) -> tuple[dict[tuple[int, int], FloorGlyphCell], int, int, int]:
    side, wx0, wy0 = _patch_extent(world)
    n = n_tiles if n_tiles is not None else side
    by_char = build_floor_patch_from_world(
        world_column_getter(world),
        wx0=wx0,
        wy0=wy0,
        n_tiles=n,
    )
    draw_map = floor_packed_draw_map_from_cells(
        by_char,
        0,
        0,
        n_tiles=n,
        get_column=world_column_getter(world),
        wx0=wx0,
        wy0=wy0,
        cam_tx=0,
        cam_ty=0,
        slot_view=slot_view,
    )
    return draw_map, wx0, wy0, n


def _fit_view_scale(span_u: int, span_v: int, view_rect, *, base_cw: int = 10, base_ch: int = 16) -> int:
    margin = 8
    avail_w = max(1, view_rect.w - margin * 2)
    avail_h = max(1, view_rect.h - margin * 2)
    for scale in (3, 2, 1):
        if span_u * base_cw * scale <= avail_w and span_v * base_ch * scale <= avail_h:
            return scale
    return 1


def draw_diag_viewport(
    surf: pygame.Surface,
    *,
    world: EditableWorld,
    view_rect,
    view_scale: int | None = None,
    font: pygame.font.Font | None = None,
    selected_tile: tuple[int, int] | None = None,
) -> DiagViewportLayout:
    """Draw full patch as diag 3×2 stamp packed layout."""
    from src.engine.layout.golden import resolve_tile_slot_view
    from src.engine.layout.screen_slots import packed_pick_map_from_slot_view

    slot_view = resolve_tile_slot_view(n_tiles=_patch_extent(world)[0], cam_tx=0, cam_ty=0)
    draw_map, wx0, wy0, n_tiles = build_world_packed_draw_map(world, slot_view=slot_view)
    packed_tile_at = packed_pick_map_from_slot_view(slot_view)

    layout_offsets = [layout_cell_to_screen(col, row) for col, row in draw_map]
    min_u = min(u for u, _v in layout_offsets)
    max_u = max(u for u, _v in layout_offsets)
    min_v = min(v for _u, v in layout_offsets)
    max_v = max(v for _u, v in layout_offsets)
    span_u = max(1, max_u - min_u + 1)
    span_v = max(1, max_v - min_v + 1)

    scale = view_scale if view_scale is not None else _fit_view_scale(span_u, span_v, view_rect)
    cell_w = max(4, PRESET_NORMAL.cell_w * scale)
    cell_h = max(6, PRESET_NORMAL.cell_h * scale)
    if font is None:
        font = pygame.font.SysFont("consolas", max(6, cell_h - 2))

    margin = 8
    ox = view_rect.x + margin - min_u * cell_w
    oy = view_rect.y + margin - min_v * cell_h

    pygame.draw.rect(surf, (10, 12, 18), (view_rect.x, view_rect.y, view_rect.w, view_rect.h))
    draw_packed_floor_map(
        surf,
        draw_map,
        ox=ox,
        oy=oy,
        cell_w=cell_w,
        cell_h=cell_h,
        font=font,
    )
    pygame.draw.rect(surf, (55, 60, 80), (view_rect.x, view_rect.y, view_rect.w, view_rect.h), 1)

    if selected_tile is not None:
        sel_wx, sel_wy = selected_tile
        sel_tx = sel_wx - wx0
        sel_ty = sel_wy - wy0
        for slot in range(4):
            row, col = slot_view[(sel_tx, sel_ty, slot)]
            lu, lv = layout_cell_to_screen(col, row)
            px = ox + lu * cell_w
            py = oy + lv * cell_h
            pygame.draw.rect(surf, (255, 220, 80), (px, py, cell_w, cell_h), 2)

    return DiagViewportLayout(
        ox=ox,
        oy=oy,
        cell_w=cell_w,
        cell_h=cell_h,
        draw_map=draw_map,
        packed_tile_at=packed_tile_at,
        wx0=wx0,
        wy0=wy0,
        n_tiles=n_tiles,
    )


def pick_diag_tile_at_panel(
    mx: int,
    my: int,
    *,
    layout: DiagViewportLayout,
    view_rect,
) -> tuple[int, int] | None:
    """Pick world diag tile (whole 3×2 stamp), not a single layout glyph."""
    if not view_rect.collide(mx, my):
        return None
    for (col, row), (tx, ty) in layout.packed_tile_at.items():
        su, sv = layout_cell_to_screen(col, row)
        px = layout.ox + su * layout.cell_w
        py = layout.oy + sv * layout.cell_h
        if px <= mx < px + layout.cell_w and py <= my < py + layout.cell_h:
            return (layout.wx0 + tx, layout.wy0 + ty)

    best_tile: tuple[int, int] | None = None
    best_d2 = 10**9
    for (col, row), (tx, ty) in layout.packed_tile_at.items():
        su, sv = layout_cell_to_screen(col, row)
        cx = layout.ox + su * layout.cell_w + layout.cell_w // 2
        cy = layout.oy + sv * layout.cell_h + layout.cell_h // 2
        d2 = (mx - cx) ** 2 + (my - cy) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best_tile = (layout.wx0 + tx, layout.wy0 + ty)
    max_d2 = (layout.cell_w * layout.cell_h) ** 2
    if best_d2 > max_d2:
        return None
    return best_tile


# Legacy alias
pick_diag_at_panel = pick_diag_tile_at_panel
