"""Level editor diag viewport tests."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def level_editor_ui_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    import pygame

    from src.characters import editor_fonts
    from src.constants import init_paths

    editor_fonts._UI_CACHE.clear()
    editor_fonts._MONO_CACHE.clear()
    editor_fonts._ICON_CACHE.clear()
    init_paths(str(ROOT))
    pygame.init()
    yield pygame
    pygame.quit()
    editor_fonts._UI_CACHE.clear()
    editor_fonts._MONO_CACHE.clear()
    editor_fonts._ICON_CACHE.clear()


@pytest.mark.unit
def test_palette_tree_draw_accepts_tuner_rect(level_editor_ui_env):
    """Regression: pygame.draw.rect needs (x,y,w,h), not tuner_ui.Rect."""
    import pygame

    from src.characters.editor_fonts import editor_ui_font
    from src.characters.tuner_ui import Rect
    from src.world.editor.state import LevelEditorState
    from src.world.editor.ui.palette_tree import LevelPaletteTree

    state = LevelEditorState()
    state.expanded_folders = {"tools", "floor", "structures", "generators"}
    palette = LevelPaletteTree()
    surf = pygame.Surface((160, 600))
    rect = Rect(0, 0, 160, 600)
    font = editor_ui_font(13)
    small = editor_ui_font(11)

    palette.draw(surf, state=state, rect=rect, font=font, small=small)
    assert len(palette._hits) > 0


@pytest.mark.unit
def test_diag_viewport_uses_stamp_layout(level_editor_ui_env):
    """5×5 patch: packed cells = solid char cells, tile (0,0) anchor top-left."""
    import pygame

    from src.characters.editor_floor import floor_solid_char_cells
    from src.characters.tuner_ui import Rect
    from src.engine.layout.screen_slots import tile_slot_packed_pos
    from src.world.editor.editable_world import EditableWorld
    from src.world.editor.generators import fill_biome
    from src.world.editor.ui.viewport import build_world_packed_draw_map, draw_diag_viewport

    world = EditableWorld(seed=1, width=5, height=5)
    world.fill_blank_grass()
    fill_biome(world, "meadow", trees=False)
    draw_map, _wx0, _wy0, n = build_world_packed_draw_map(world)
    assert n == 5
    from src.engine.layout.golden import resolve_tile_slot_view

    assert len(draw_map) == len(resolve_tile_slot_view(n_tiles=5))
    assert tile_slot_packed_pos(0, 0, 0) in draw_map

    layout = draw_diag_viewport(
        pygame.Surface((600, 400)),
        world=world,
        view_rect=Rect(0, 0, 600, 400),
    )
    assert layout.n_tiles == 5
    assert len(layout.draw_map) == len(resolve_tile_slot_view(n_tiles=5))


@pytest.mark.unit
def test_default_patch_is_5m(level_editor_ui_env):
    from src.constants import TILES_PER_M_XY
    from src.engine.config import DEFAULT_EDITOR_FLOOR_METERS, editor_floor_patch_tiles
    from src.world.editor.editable_world import EditableWorld

    assert DEFAULT_EDITOR_FLOOR_METERS == 5.0
    side = editor_floor_patch_tiles()
    assert side == int(DEFAULT_EDITOR_FLOOR_METERS * TILES_PER_M_XY)
    world = EditableWorld(seed=0)
    assert world.bounds.width == side


@pytest.mark.unit
def test_pick_selects_whole_diag_tile(level_editor_ui_env):
    import pygame

    from src.characters.tuner_ui import Rect
    from src.engine.projection.packed import layout_cell_to_screen
    from src.world.editor.editable_world import EditableWorld
    from src.world.editor.ui.viewport import build_world_packed_draw_map, draw_diag_viewport, pick_diag_tile_at_panel

    world = EditableWorld(seed=1, width=5, height=5)
    world.fill_blank_grass()
    surf = pygame.Surface((600, 400))
    view_rect = Rect(0, 0, 600, 400)
    layout = draw_diag_viewport(surf, world=world, view_rect=view_rect)

    draw_map, wx0, wy0, _n = build_world_packed_draw_map(world)
    target_tx, target_ty = 2, 2
    cells = [
        (col, row)
        for (col, row), cell in draw_map.items()
        if cell.tile_tx == target_tx and cell.tile_ty == target_ty
    ]
    assert len(cells) >= 2
    for col, row in cells:
        su, sv = layout_cell_to_screen(col, row)
        mx = layout.ox + su * layout.cell_w + layout.cell_w // 2
        my = layout.oy + sv * layout.cell_h + layout.cell_h // 2
        picked = pick_diag_tile_at_panel(mx, my, layout=layout, view_rect=view_rect)
        assert picked == (wx0 + target_tx, wy0 + target_ty)


@pytest.mark.unit
def test_large_patch_is_single_per_tile_diamond(level_editor_ui_env):
    """Whole patch: per-tile slots on one diamond, not copied 5×5 chunks."""
    from src.engine.config import FLOOR_LAYOUT_TILES
    from src.world.editor.editable_world import EditableWorld
    from src.world.editor.ui.viewport import build_world_packed_draw_map

    n = 25
    world = EditableWorld(seed=3, width=n, height=n)
    world.fill_blank_grass()
    draw_map, _wx0, _wy0, side = build_world_packed_draw_map(world)
    assert side == n
    from src.characters.editor_floor import floor_solid_char_cells

    from src.engine.layout.screen_slots import build_tile_slot_screen_map

    assert len(draw_map) == len(build_tile_slot_screen_map(n))

    rows: dict[int, list[int]] = {}
    for (col, row), _cell in draw_map.items():
        rows.setdefault(row, []).append(col)
    row_widths = tuple(max(cols) - min(cols) + 1 for _r, cols in sorted(rows.items()))
    assert row_widths[0] < max(row_widths)
    assert row_widths[-1] < max(row_widths)
    assert len(row_widths) > 2 * FLOOR_LAYOUT_TILES


@pytest.mark.unit
def test_select_tool_is_default(level_editor_ui_env):
    from src.world.editor.state import LevelEditorState

    state = LevelEditorState()
    assert state.active_tool == "select"


@pytest.mark.unit
def test_level_editor_run_smoke_frame(level_editor_ui_env):
    import sys

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "level_editor",
        ROOT / "scripts" / "level_editor.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.run_smoke_frame(seed=7, size=10) == 0
