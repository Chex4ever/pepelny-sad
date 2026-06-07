"""Editor floor: packed layout diamond matches golden; not iso-projected rectangle."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_floor_patch_has_25_tiles_60_stamp_cells():
    from src.characters.editor_floor import (
        build_floor_patch,
        floor_solid_char_cells,
        floor_tile_anchors,
    )
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    patch = build_floor_patch(0, 0, seed=2)
    solid = floor_solid_char_cells(0, 0)
    assert len(floor_tile_anchors(0, 0)) == EDITOR_FLOOR_TILES ** 2
    assert len(solid) == 60
    assert len(patch) == 60


@pytest.mark.unit
def test_editor_floor_draw_matches_golden_diamond_silhouette():
    """character_editor must draw the same 19×10 diamond as EDITOR_FLOOR_5X5_TILE_REFERENCE."""
    from src.characters.editor_floor import (
        assert_floor_has_no_holes,
        floor_packed_draw_map,
        floor_row_gap_count,
        packed_canvas_row_gap_count,
        rasterize_floor_packed_view,
    )
    from src.characters.editor_floor_test_tiles import (
        EDITOR_FLOOR_5X5_TILE_LAYOUT_ROW_WIDTHS,
        EDITOR_FLOOR_5X5_TILE_REFERENCE,
        packed_layout_silhouette,
    )

    silhouette = packed_layout_silhouette()
    draw = floor_packed_draw_map(0, 0, seed=0)
    assert set(draw.keys()) == set(silhouette)
    assert len(silhouette) == 100

    by_row: dict[int, list[int]] = {}
    for col, row in silhouette:
        by_row.setdefault(row, []).append(col)
    row_widths = tuple(max(cols) - min(cols) + 1 for row, cols in sorted(by_row.items()))
    assert row_widths == EDITOR_FLOOR_5X5_TILE_LAYOUT_ROW_WIDTHS
    assert row_widths == (2, 6, 10, 14, 18, 18, 14, 10, 6, 2)
    assert floor_row_gap_count(silhouette) == 0

    assert_floor_has_no_holes(0, 0)
    packed = rasterize_floor_packed_view(0, 0)
    assert packed == EDITOR_FLOOR_5X5_TILE_REFERENCE
    assert packed_canvas_row_gap_count(packed) == 0


@pytest.mark.unit
def test_iso_projection_is_not_editor_floor_shape():
    """Raw iso (su, sv) is a skewed rectangle — not the packed layout diamond."""
    from src.characters.editor_floor import floor_iso_view_offsets, floor_row_gap_count
    from src.characters.editor_floor_test_tiles import packed_layout_silhouette

    iso = floor_iso_view_offsets(0, 0)
    assert floor_row_gap_count(iso) > 0
    by_row: dict[int, list[int]] = {}
    for u, v in iso:
        by_row.setdefault(v, []).append(u)
    iso_widths = {v: max(us) - min(us) + 1 for v, us in by_row.items()}
    assert len(set(iso_widths.values())) == 1, "iso span-fill rows are equal width (rectangle)"

    sil = packed_layout_silhouette()
    by_row2: dict[int, list[int]] = {}
    for col, row in sil:
        by_row2.setdefault(row, []).append(col)
    sil_widths = {row: max(cols) - min(cols) + 1 for row, cols in by_row2.items()}
    assert len(set(sil_widths.values())) > 1, "golden diamond has varying row widths"


@pytest.mark.unit
def test_world_tile_aligns_with_stamp_tip_after_focus():
    from src.characters.editor_floor import floor_screen_offset, floor_tile_anchors
    from src.prototype.dia_scale.tessellation import stamp_tip
    from src.render.iso_character_view import EDITOR_FLOOR_TILES
    from src.render.iso_projector import IsoProjector

    p = IsoProjector(origin_x=60, origin_y=40)
    fx, fy = 10, 10
    center = EDITOR_FLOOR_TILES // 2
    feet_sx, feet_sy = p.world_to_screen(fx, fy, focus_wx=fx, focus_wy=fy)
    center_anchor = next(
        a for a in floor_tile_anchors(fx, fy) if a[0] == center and a[1] == center
    )
    su, sv = floor_screen_offset(center_anchor[2], center_anchor[3], ref_cx=fx, ref_cy=fy)
    assert (su, sv) == (0, 0)
    assert (feet_sx, feet_sy) == (p.origin_x, p.origin_y)
    assert stamp_tip(center, center) == (0, 4)


@pytest.mark.unit
def test_renderer_uses_packed_layout_draw_map():
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.editor_floor import floor_packed_draw_map, floor_packed_layout_offsets
    from src.characters.editor_floor_test_tiles import packed_layout_silhouette
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

    model = bake_voxel_model(CharacterSpec("human", 42, 30), pose_id="idle_s")
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=400, panel_h=400)
    feet_cx, feet_cy = int(model.anchor_x), int(model.anchor_y)
    renderer.render(model, show_floor=True, show_shading=False, show_diagnostics=False, floor_seed=11)

    draw = floor_packed_draw_map(feet_cx, feet_cy, seed=11)
    assert set(draw.keys()) == set(packed_layout_silhouette())
    assert len(floor_packed_layout_offsets(feet_cx, feet_cy, seed=11)) == 100
    pygame.quit()


@pytest.mark.unit
def test_stamp_origin_is_diag_regression():
    from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

    assert stamp_origin(1, 0) == (0, 0)
    assert stamp_tip(1, 0) == (1, 1)
    assert stamp_origin(1, 0) != (2, 0)
