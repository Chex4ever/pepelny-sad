"""Editor floor: packed layout diamond matches golden; not iso-projected rectangle."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_floor_patch_1m_has_25_tiles_60_stamp_cells():
    from src.characters.editor_floor import (
        build_floor_patch,
        floor_solid_char_cells,
        floor_tile_anchors,
    )
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    n = EDITOR_FLOOR_TILES
    patch = build_floor_patch(0, 0, n_tiles=n, seed=2)
    solid = floor_solid_char_cells(0, 0, n_tiles=n)
    assert len(floor_tile_anchors(0, 0, n_tiles=n)) == n ** 2
    assert len(solid) == 60
    assert len(patch) == 60


@pytest.mark.unit
def test_engine_patch_tiles_default_is_5m():
    from src.constants import TILES_PER_M_XY
    from src.engine.config import (
        DEFAULT_EDITOR_FLOOR_METERS,
        EDITOR_FLOOR_TILES,
        editor_floor_patch_tiles,
    )

    n = editor_floor_patch_tiles()
    assert n == int(DEFAULT_EDITOR_FLOOR_METERS * TILES_PER_M_XY)
    assert n == 25
    assert EDITOR_FLOOR_TILES == 5


@pytest.mark.unit
def test_character_floor_is_1m_layout_unit():
    from src.characters.editor_floor import floor_solid_char_cells, floor_tile_anchors
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    n = EDITOR_FLOOR_TILES
    assert n == 5
    assert len(floor_tile_anchors(0, 0, n_tiles=n)) == n ** 2
    assert len(floor_solid_char_cells(0, 0, n_tiles=n)) == 60


@pytest.mark.unit
def test_editor_floor_draw_uses_tile_stamp_layout():
    """5×5 patch: one packed cell per solid char; tile (0,0) is stamp not a line."""
    from src.characters.editor_floor import (
        assert_floor_has_no_holes,
        floor_packed_draw_map,
        floor_solid_char_cells,
    )
    from src.engine.layout.screen_slots import tile_slot_packed_pos
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    n = EDITOR_FLOOR_TILES
    draw = floor_packed_draw_map(0, 0, n_tiles=n, seed=0)
    from src.engine.layout.golden import resolve_tile_slot_view

    assert len(draw) == len(resolve_tile_slot_view(n_tiles=n))
    assert_floor_has_no_holes(0, 0, n_tiles=n)

    stamp = [tile_slot_packed_pos(0, 0, s) for s in range(4)]
    assert len({c for _r, c in stamp}) > 1
    assert len({r for r, _c in stamp}) > 1
    assert all((col, row) in draw for row, col in stamp)


@pytest.mark.unit
def test_iso_projection_is_not_editor_floor_shape():
    """Raw iso (su, sv) is a skewed rectangle — not the packed layout diamond."""
    from src.characters.editor_floor import floor_iso_view_offsets, floor_row_gap_count
    from src.characters.editor_floor_test_tiles import packed_layout_silhouette
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    iso = floor_iso_view_offsets(0, 0, n_tiles=EDITOR_FLOOR_TILES)
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
    from src.render.iso_character_view import EDITOR_FLOOR_TILES
    from src.render.iso_projector import IsoProjector

    p = IsoProjector(origin_x=60, origin_y=40)
    fx, fy = 10, 10
    center = EDITOR_FLOOR_TILES // 2
    feet_sx, feet_sy = p.world_to_screen(fx, fy, focus_wx=fx, focus_wy=fy)
    center_anchor = next(
        a for a in floor_tile_anchors(fx, fy, n_tiles=EDITOR_FLOOR_TILES)
        if a[0] == center and a[1] == center
    )
    su, sv = floor_screen_offset(center_anchor[2], center_anchor[3], ref_cx=fx, ref_cy=fy)
    assert (su, sv) == (0, 0)
    assert (feet_sx, feet_sy) == (p.origin_x, p.origin_y)


@pytest.mark.unit
def test_renderer_uses_packed_layout_draw_map():
    import pygame

    pygame.init()
    from src.characters.bake import bake_voxel_model
    from src.characters.editor_floor import floor_packed_draw_map, floor_packed_layout_offsets
    from src.characters.spec import CharacterSpec
    from src.prototype.dia_scale.display_scale import PRESET_NORMAL
    from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer
    from src.render.iso_character_view import EDITOR_FLOOR_TILES

    model = bake_voxel_model(CharacterSpec("human", 42, 30), pose_id="idle_s")
    renderer = IsoCharacterRenderer(preset=PRESET_NORMAL, panel_w=400, panel_h=400)
    feet_cx, feet_cy = int(model.anchor_x), int(model.anchor_y)
    renderer.render(model, show_floor=True, show_shading=False, show_diagnostics=False, floor_seed=11)

    draw = floor_packed_draw_map(feet_cx, feet_cy, seed=11)
    from src.characters.editor_floor import floor_solid_char_cells

    from src.engine.layout.golden import resolve_tile_slot_view

    assert len(draw) == len(resolve_tile_slot_view(n_tiles=EDITOR_FLOOR_TILES))
    assert len(floor_packed_layout_offsets(
        feet_cx, feet_cy, n_tiles=EDITOR_FLOOR_TILES, seed=11
    )) == len(resolve_tile_slot_view(n_tiles=EDITOR_FLOOR_TILES))
    pygame.quit()


@pytest.mark.unit
def test_stamp_origin_is_diag_regression():
    from src.prototype.dia_scale.tessellation import stamp_origin, stamp_tip

    assert stamp_origin(1, 0) == (0, 0)
    assert stamp_tip(1, 0) == (1, 1)
    assert stamp_origin(1, 0) != (2, 0)
