"""Editor floor: diag stamp tessellation, iso screen draw, layout golden."""
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
def test_floor_iso_screen_draw_has_no_row_gaps():
    """What character_editor draws: span-filled iso screen must have zero row gaps."""
    from src.characters.editor_floor import (
        assert_floor_has_no_holes,
        floor_iso_draw_map,
        floor_iso_view_offsets,
        floor_iso_view_offsets_span_filled,
        floor_row_gap_count,
        floor_solid_has_internal_holes,
        packed_canvas_row_gap_count,
        rasterize_floor_packed_view,
    )
    from src.characters.editor_floor_test_tiles import EDITOR_FLOOR_5X5_TILE_REFERENCE

    raw = floor_iso_view_offsets(0, 0)
    assert floor_row_gap_count(raw) > 0, "raw @ projection has gaps (expected before span fill)"

    span = floor_iso_view_offsets_span_filled(0, 0)
    assert floor_row_gap_count(span) == 0
    assert floor_solid_has_internal_holes(0, 0) == []
    assert len(floor_iso_draw_map(0, 0)) == len(span)

    assert_floor_has_no_holes(0, 0)
    assert_floor_has_no_holes(10, 20)
    assert_floor_has_no_holes(-3, 7)

    packed = rasterize_floor_packed_view(0, 0)
    assert packed == EDITOR_FLOOR_5X5_TILE_REFERENCE
    assert packed_canvas_row_gap_count(packed) == 0


@pytest.mark.unit
def test_world_tile_aligns_with_stamp_tip_after_focus():
    """At focus, overworld anchor matches editor center tile stamp tip (same iso step)."""
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
    for dx, dy in ((1, 0), (0, 1), (1, -1)):
        wx, wy = fx + dx, fy + dy
        sx, sy = p.world_to_screen(wx, wy, focus_wx=fx, focus_wy=fy)
        assert (sx - feet_sx, sy - feet_sy) == (
            int(round((dx - dy) * 2)),
            int(round(dx + dy)),
        )


@pytest.mark.unit
def test_floor_screen_offset_matches_iso_formula():
    from src.characters.editor_floor import floor_screen_offset, floor_tile_anchors

    for _tx, _ty, ax, ay in floor_tile_anchors(10, 20):
        su, sv = floor_screen_offset(ax, ay, ref_cx=10, ref_cy=20)
        dx, dy = ax - 10, ay - 20
        assert su == int(round((dx - dy) * 2))
        assert sv == int(round((dx + dy) * 1))


@pytest.mark.unit
def test_renderer_draws_span_filled_iso_floor():
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.editor_floor import (
        build_floor_patch,
        floor_iso_draw_map,
        floor_iso_view_offsets_span_filled,
    )
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

    model = bake_voxel_model(CharacterSpec("human", 42, 30), pose_id="idle_s")
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=400, panel_h=400)
    feet_cx, feet_cy = int(model.anchor_x), int(model.anchor_y)
    build_floor_patch(feet_cx, feet_cy, seed=11)
    renderer.render(model, show_floor=True, show_shading=False, show_diagnostics=False, floor_seed=11)

    span = floor_iso_view_offsets_span_filled(feet_cx, feet_cy)
    assert set(floor_iso_draw_map(feet_cx, feet_cy, seed=11)) == span
    pygame.quit()


@pytest.mark.unit
def test_stamp_origin_is_diag_regression():
    from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

    assert stamp_origin(1, 0) == (0, 0)
    assert stamp_tip(1, 0) == (1, 1)
    assert stamp_origin(1, 0) != (2, 0)
