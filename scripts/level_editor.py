#!/usr/bin/env python3
"""Level editor — WYSIWYG surface map editor (CPU iso, character-editor layout).

Run from repo root:
  python scripts/level_editor.py
  python scripts/level_editor.py --load maps/test.json

Layout: palette (left) | iso viewport (center) | inspector (right) | status bar.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.characters.editor_fonts import editor_mono_font, editor_ui_font
from src.characters.tuner_ui import COLOR_BG, Rect
from src.constants import init_paths
from src.engine.config import editor_floor_patch_tiles
from src.prototype.dia_scale.display_scale import (
    EDITOR_ANIM_H,
    EDITOR_PARAMS_W,
    EDITOR_PARTS_W,
    EDITOR_VIEW_H,
    EDITOR_VIEW_W,
    EDITOR_WINDOW_PX_H,
    EDITOR_WINDOW_PX_W,
)
from src.world.editor.document import load_map, save_map
from src.world.editor.editable_world import EditableWorld
from src.world.editor.generators import (
    fill_biome,
    make_clearing,
    paint_road,
    scatter_bushes_in_bounds,
    scatter_trees,
)
from src.world.editor.state import LevelEditorState
from src.world.editor.tools import EditorTools
from src.world.editor.ui.inspector import LevelInspectorPanel
from src.world.editor.ui.palette_tree import LevelPaletteTree
from src.world.editor.ui.status_bar import LevelStatusBar
from src.world.editor.ui.viewport import (
    DiagViewportLayout,
    draw_diag_viewport,
    pick_diag_at_panel,
)

DEFAULT_MAP_DIR = os.path.join(ROOT, "maps")


def _new_world(*, seed: int = 0, size: int | None = None) -> EditableWorld:
    side = size if size is not None else editor_floor_patch_tiles()
    world = EditableWorld(seed=seed, width=side, height=side, wx0=0, wy0=0)
    world.fill_blank_grass()
    return world


def _in_bounds(world: EditableWorld, wx: int, wy: int) -> bool:
    b = world.bounds
    return b.wx0 <= wx < b.wx0 + b.width and b.wy0 <= wy < b.wy0 + b.height


def _sync_tools(tools: EditorTools, state: LevelEditorState) -> None:
    tools.active_stencil = state.active_stencil
    tools.active_structure = state.active_structure


def _apply_tool_at(
    tools: EditorTools,
    state: LevelEditorState,
    inspector: LevelInspectorPanel,
    world: EditableWorld,
    wx: int,
    wy: int,
) -> None:
    tool = state.active_tool
    biome = inspector.biome_id
    if tool == "paint":
        tools.paint_floor(wx, wy)
    elif tool == "erase":
        tools.erase_cell(wx, wy)
    elif tool == "structure":
        tools.place_structure_at(wx, wy)
    elif tool == "tree":
        tools.place_tree(wx, wy, biome_id=biome)
    elif tool == "road":
        state.road_points.append((wx, wy))
        if len(state.road_points) >= 2:
            paint_road(world, state.road_points)
            state.road_points.clear()
    elif tool == "gen_biome":
        fill_biome(world, biome, trees=False)
    elif tool == "gen_trees":
        scatter_trees(world, biome_id=biome)
    elif tool == "gen_bushes":
        scatter_bushes_in_bounds(world)
    elif tool == "gen_clearing":
        make_clearing(world, wx - 1, wy - 1, 3, 3)


def _render_frame(
    screen: pygame.Surface,
    *,
    world: EditableWorld,
    state: LevelEditorState,
    inspector: LevelInspectorPanel,
    palette: LevelPaletteTree,
    status_bar: LevelStatusBar,
    font,
    small,
    mono,
    palette_rect: Rect,
    view_rect: Rect,
    inspector_rect: Rect,
    status_rect: Rect,
    view_scale: int = 2,
) -> DiagViewportLayout:
    screen.fill(COLOR_BG)
    palette.draw(screen, state=state, rect=palette_rect, font=font, small=small)
    selected_tile = None
    if state.selected_wx is not None and state.selected_wy is not None:
        selected_tile = (state.selected_wx, state.selected_wy)
    layout = draw_diag_viewport(
        screen,
        world=world,
        view_rect=view_rect,
        view_scale=None,
        font=small,
        selected_tile=selected_tile,
    )
    inspector.draw(
        screen, state=state, world=world, rect=inspector_rect, font=font, small=small,
    )
    status_bar.draw(
        screen,
        rect=status_rect,
        lines=[
            f"diag 3×2 packed | patch {world.bounds.width}×{world.bounds.height} tiles",
            "Выделение: клик = тайл | шаблон — в свойствах → палитра",
            f"seed={world.seed} biome={inspector.biome_id} map={state.map_path or '(новая)'}",
            "+/- размер | WASD pan focus | Ctrl+S/O save/load",
        ],
        small=mono,
    )
    pygame.display.flip()
    return layout


def run_smoke_frame(*, seed: int = 4242, size: int = 10) -> int:
    """Init window + draw one full frame (CI / regression)."""
    init_paths(ROOT)
    os.environ.setdefault("PEPELNY_RENDER", "iso")
    pygame.init()

    state = LevelEditorState()
    inspector = LevelInspectorPanel()
    state.active_biome = inspector.biome_id
    world = _new_world(seed=seed, size=size)
    fill_biome(world, inspector.biome_id, trees=False)

    palette = LevelPaletteTree()
    status_bar = LevelStatusBar()
    font = editor_ui_font(13)
    small = editor_ui_font(11)
    mono = editor_mono_font(10)

    screen = pygame.display.set_mode((EDITOR_WINDOW_PX_W, EDITOR_WINDOW_PX_H))
    palette_rect = Rect(0, 0, EDITOR_PARTS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    view_rect = Rect(EDITOR_PARTS_W, 0, EDITOR_VIEW_W, EDITOR_VIEW_H)
    inspector_rect = Rect(EDITOR_PARTS_W + EDITOR_VIEW_W, 0, EDITOR_PARAMS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    status_rect = Rect(0, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H, EDITOR_WINDOW_PX_W, EDITOR_ANIM_H)

    _render_frame(
        screen,
        world=world,
        state=state,
        inspector=inspector,
        palette=palette,
        status_bar=status_bar,
        font=font,
        small=small,
        mono=mono,
        palette_rect=palette_rect,
        view_rect=view_rect,
        inspector_rect=inspector_rect,
        status_rect=status_rect,
        view_scale=2,
    )
    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Surface level editor")
    parser.add_argument("--load", metavar="PATH", help="Load map JSON")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--size", type=int, default=None, help="Patch side in tiles")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Init + one frame + exit 0 (CI smoke test)",
    )
    args = parser.parse_args()

    if args.smoke:
        return run_smoke_frame(seed=args.seed, size=args.size or 10)

    init_paths(ROOT)
    os.environ.setdefault("PEPELNY_RENDER", "iso")
    pygame.init()

    state = LevelEditorState()
    inspector = LevelInspectorPanel()
    state.active_biome = inspector.biome_id

    if args.load and os.path.isfile(args.load):
        doc = load_map(args.load)
        world = EditableWorld(
            seed=doc.seed,
            width=doc.bounds.width,
            height=doc.bounds.height,
            wx0=doc.bounds.wx0,
            wy0=doc.bounds.wy0,
        )
        world.doc = doc
        state.map_path = args.load
    else:
        world = _new_world(seed=args.seed, size=args.size)
        fill_biome(world, inspector.biome_id, trees=False)

    tools = EditorTools(world)
    _sync_tools(tools, state)

    palette = LevelPaletteTree()
    status_bar = LevelStatusBar()
    font = editor_ui_font(13)
    small = editor_ui_font(11)
    mono = editor_mono_font(10)

    screen = pygame.display.set_mode((EDITOR_WINDOW_PX_W, EDITOR_WINDOW_PX_H))
    pygame.display.set_caption("level_editor [diag 3×2 packed]")

    palette_rect = Rect(0, 0, EDITOR_PARTS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    view_rect = Rect(EDITOR_PARTS_W, 0, EDITOR_VIEW_W, EDITOR_VIEW_H)
    inspector_rect = Rect(EDITOR_PARTS_W + EDITOR_VIEW_W, 0, EDITOR_PARAMS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    status_rect = Rect(0, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H, EDITOR_WINDOW_PX_W, EDITOR_ANIM_H)

    viewport_layout: DiagViewportLayout | None = None

    running = True
    while running:
        fx, fy = world.focus()
        mx, my = pygame.mouse.get_pos()
        pan_dx = pan_dy = 0

        def on_ui_change() -> None:
            _sync_tools(tools, state)
            state.active_biome = inspector.biome_id

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                continue

            if palette.handle_event(
                ev, state=state, on_change=on_ui_change, mx=mx, my=my, rect=palette_rect,
            ):
                _sync_tools(tools, state)
                continue

            if inspector.handle_event(
                ev, state=state, world=world, on_change=on_ui_change, mx=mx, my=my, rect=inspector_rect,
            ):
                state.active_biome = inspector.biome_id
                continue

            if ev.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_n and not (mods & pygame.KMOD_CTRL):
                    world = _new_world(seed=args.seed, size=world.bounds.width)
                    tools = EditorTools(world)
                    _sync_tools(tools, state)
                    state.map_path = None
                    state.clear_selection()
                    fill_biome(world, inspector.biome_id, trees=False)
                elif ev.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                    os.makedirs(DEFAULT_MAP_DIR, exist_ok=True)
                    if not state.map_path:
                        state.map_path = os.path.join(DEFAULT_MAP_DIR, f"map_s{world.seed}.json")
                    save_map(state.map_path, world.doc)
                elif ev.key == pygame.K_o and (mods & pygame.KMOD_CTRL):
                    load_path = state.map_path or os.path.join(DEFAULT_MAP_DIR, "map.json")
                    if os.path.isfile(load_path):
                        doc = load_map(load_path)
                        world = EditableWorld(
                            seed=doc.seed,
                            width=doc.bounds.width,
                            height=doc.bounds.height,
                            wx0=doc.bounds.wx0,
                            wy0=doc.bounds.wy0,
                        )
                        world.doc = doc
                        tools = EditorTools(world)
                        _sync_tools(tools, state)
                        state.map_path = load_path
                elif ev.key == pygame.K_g:
                    fill_biome(world, inspector.biome_id, trees=False)
                elif ev.key == pygame.K_r:
                    world.doc.seed = (world.doc.seed * 1103515245 + 12345) & 0x7FFFFFFF
                    fill_biome(world, inspector.biome_id, trees=True)
                elif ev.key in (pygame.K_LEFT, pygame.K_a) and not view_rect.collide(mx, my):
                    pan_dx = -1
                elif ev.key in (pygame.K_RIGHT, pygame.K_d) and not view_rect.collide(mx, my):
                    pan_dx = 1
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    pan_dy = -1
                elif ev.key in (pygame.K_DOWN, pygame.K_s) and not (mods & pygame.KMOD_CTRL):
                    pan_dy = 1
                elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    side = min(world.bounds.width + 2, 64)
                    world.doc.bounds.width = side
                    world.doc.bounds.height = side
                    world.fill_blank_grass()
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    side = max(8, world.bounds.width - 2)
                    world.doc.bounds.width = side
                    world.doc.bounds.height = side

            elif ev.type == pygame.MOUSEBUTTONDOWN and view_rect.collide(mx, my):
                if viewport_layout is None:
                    continue
                picked = pick_diag_at_panel(
                    mx, my, layout=viewport_layout, view_rect=view_rect,
                )
                if not picked or not _in_bounds(world, *picked):
                    continue
                wx, wy = picked
                if ev.button == 1:
                    if state.active_tool == "select":
                        state.select_tile(wx, wy)
                    else:
                        state.select_tile(wx, wy)
                        _apply_tool_at(tools, state, inspector, world, wx, wy)
                elif ev.button == 3:
                    if state.active_tool != "select":
                        tools.erase_cell(wx, wy)
                    state.select_tile(wx, wy)

        if pan_dx or pan_dy:
            world.pan_focus(pan_dx, pan_dy)

        viewport_layout = _render_frame(
            screen,
            world=world,
            state=state,
            inspector=inspector,
            palette=palette,
            status_bar=status_bar,
            font=font,
            small=small,
            mono=mono,
            palette_rect=palette_rect,
            view_rect=view_rect,
            inspector_rect=inspector_rect,
            status_rect=status_rect,
            view_scale=2,
        )

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
