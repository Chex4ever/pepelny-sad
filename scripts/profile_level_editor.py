#!/usr/bin/env python3
"""Profile level editor frame cost (headless pygame)."""
from __future__ import annotations

import cProfile
import os
import pstats
import sys
from io import StringIO

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
from src.world.editor.editable_world import EditableWorld
from src.world.editor.generators import fill_biome
from src.world.editor.state import LevelEditorState
from src.world.editor.ui.inspector import LevelInspectorPanel
from src.world.editor.ui.palette_tree import LevelPaletteTree
from src.world.editor.ui.status_bar import LevelStatusBar
from src.world.editor.ui.viewport import draw_diag_viewport


def _setup(*, size: int | None = None):
    init_paths(ROOT)
    os.environ.setdefault("PEPELNY_RENDER", "iso")
    pygame.init()
    side = size if size is not None else editor_floor_patch_tiles()
    world = EditableWorld(seed=4242, width=side, height=side)
    world.fill_blank_grass()
    fill_biome(world, "meadow", trees=False)
    state = LevelEditorState()
    state.select_tile(world.bounds.wx0 + side // 2, world.bounds.wy0 + side // 2)
    inspector = LevelInspectorPanel()
    palette = LevelPaletteTree()
    status_bar = LevelStatusBar()
    font = editor_ui_font(13)
    small = editor_ui_font(11)
    mono = editor_mono_font(10)
    screen = pygame.Surface((EDITOR_WINDOW_PX_W, EDITOR_WINDOW_PX_H))
    palette_rect = Rect(0, 0, EDITOR_PARTS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    view_rect = Rect(EDITOR_PARTS_W, 0, EDITOR_VIEW_W, EDITOR_VIEW_H)
    inspector_rect = Rect(
        EDITOR_PARTS_W + EDITOR_VIEW_W, 0, EDITOR_PARAMS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H,
    )
    status_rect = Rect(0, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H, EDITOR_WINDOW_PX_W, EDITOR_ANIM_H)
    return (
        screen,
        world,
        state,
        inspector,
        palette,
        status_bar,
        font,
        small,
        mono,
        palette_rect,
        view_rect,
        inspector_rect,
        status_rect,
    )


def render_frame(args) -> None:
    (
        screen,
        world,
        state,
        inspector,
        palette,
        status_bar,
        font,
        small,
        mono,
        palette_rect,
        view_rect,
        inspector_rect,
        status_rect,
    ) = args
    screen.fill(COLOR_BG)
    palette.draw(screen, state=state, rect=palette_rect, font=font, small=small)
    selected = (state.selected_wx, state.selected_wy)
    draw_diag_viewport(
        screen,
        world=world,
        view_rect=view_rect,
        view_scale=None,
        font=small,
        selected_tile=selected,
    )
    inspector.draw(
        screen, state=state, world=world, rect=inspector_rect, font=font, small=small,
    )
    status_bar.draw(
        screen,
        rect=status_rect,
        lines=[
            f"patch {world.bounds.width}x{world.bounds.height}",
            "status",
            f"seed={world.seed}",
        ],
        small=mono,
    )


def profile_subsystems(*, size: int | None = None, frames: int = 30) -> None:
    import time

    from src.engine.floor.draw_map import floor_packed_draw_map_from_cells
    from src.engine.floor.world_patch import build_floor_patch_from_world, world_column_getter
    from src.engine.layout.screen_slots import build_packed_tile_pick_map, build_tile_slot_screen_map
    from src.engine.viewport.floor import draw_packed_floor_map
    from src.world.editor.ui.viewport import build_world_packed_draw_map

    init_paths(ROOT)
    os.environ.setdefault("PEPELNY_RENDER", "iso")
    pygame.init()
    side = size if size is not None else editor_floor_patch_tiles()
    world = EditableWorld(seed=4242, width=side, height=side)
    world.fill_blank_grass()
    fill_biome(world, "meadow", trees=False)
    small = editor_ui_font(11)
    n = side

    def bench(label: str, fn, reps: int = 50) -> float:
        t0 = time.perf_counter()
        for _ in range(reps):
            fn()
        ms = (time.perf_counter() - t0) / reps * 1000
        print(f"  {label:42s} {ms:8.2f} ms")
        return ms

    print(f"\n=== Subsystem bench (n={n}, {n * n * 4} draw cells) ===")
    getter = world_column_getter(world)
    wx0, wy0 = world.bounds.wx0, world.bounds.wy0

    bench("build_tile_slot_screen_map", lambda: build_tile_slot_screen_map(n))
    bench("build_packed_tile_pick_map", lambda: build_packed_tile_pick_map(n))
    bench(
        "build_floor_patch_from_world",
        lambda: build_floor_patch_from_world(getter, wx0=wx0, wy0=wy0, n_tiles=n),
    )

    by_char = build_floor_patch_from_world(getter, wx0=wx0, wy0=wy0, n_tiles=n)
    bench(
        "floor_packed_draw_map_from_cells",
        lambda: floor_packed_draw_map_from_cells(by_char, 0, 0, n_tiles=n),
    )
    draw_map, *_ = build_world_packed_draw_map(world)
    surf = pygame.Surface((800, 600))

    def draw_only():
        surf.fill((0, 0, 0))
        draw_packed_floor_map(surf, draw_map, ox=20, oy=20, cell_w=10, cell_h=16, font=small)

    bench("draw_packed_floor_map (pygame)", draw_only, reps=20)
    bench("build_world_packed_draw_map (full)", lambda: build_world_packed_draw_map(world))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=None)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--bench-only", action="store_true")
    args = parser.parse_args()

    if args.bench_only:
        profile_subsystems(size=args.size, frames=args.frames)
        return 0

    setup = _setup(size=args.size)
    world = setup[1]
    n = world.bounds.width
    print(f"Profiling {args.frames} frames, patch {n}x{n} ({n * n * 4} packed cells)")

    profile_subsystems(size=n, frames=1)

    pr = cProfile.Profile()
    pr.enable()
    for _ in range(args.frames):
        render_frame(setup)
    pr.disable()

    print(f"\n=== cProfile top 40 (cumulative) over {args.frames} frames ===")
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(40)
    print(s.getvalue())

    print(f"\n=== cProfile top 25 (tottime) ===")
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("tottime")
    ps.print_stats(25)
    print(s.getvalue())

    per_frame_ms = ps.total_tt / args.frames * 1000
    print(f"Approx frame time: {per_frame_ms:.1f} ms ({1000/per_frame_ms:.1f} FPS theoretical max)")
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
