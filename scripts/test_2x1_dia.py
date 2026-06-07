#!/usr/bin/env python3
"""Large-scale char-grid prototype: meadow or voxel tree showcase.

Run:
  python scripts/test_2x1_dia.py
  python scripts/test_2x1_dia.py --mode tree
  python scripts/test_2x1_dia.py --mode tree --export --seed 42
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import init_paths
from src.prototype.dia_scale.cross_section import (
    project_xz,
    project_yz,
    scroll_section_coord,
    slice_xz,
    slice_yz,
)
from src.prototype.dia_scale.display_scale import (
    PRESET_COMPACT,
    PRESET_NORMAL,
    WINDOW_PX_W,
    visible_chars,
)
from src.prototype.dia_scale.export_png import export_scene_png
from src.prototype.dia_scale.renderer import CharGridRenderer
from src.prototype.dia_scale.scene import build_meadow_scene, build_tree_showcase
from src.prototype.dia_scale.section_renderer import SectionRenderer, blit_split
from src.prototype.dia_scale.slice_view import SLICE_VIEW_LABELS, SliceViewMode, cycle_slice_view_mode
from src.prototype.dia_scale.tessellation import stamp_origin
from src.prototype.dia_scale.tree_voxel_gen import project_tree_at_z, project_tree_up_to_z


def _wheel_steps(ev: pygame.event.Event) -> int:
    if getattr(ev, "precise_y", 0):
        return int(round(ev.precise_y))
    y = ev.y
    if y == 0:
        return 0
    return y // 120 or (1 if y > 0 else -1)


def _clamp_slice_z(z: int, z_max: int) -> int:
    return max(0, min(z_max, z))


def _default_focus(nx: int, ny: int) -> tuple[int, int]:
    ox, oy = stamp_origin(nx // 2, ny // 2)
    return ox + 1, oy + 1


def run_export(args: argparse.Namespace) -> int:
    out_dir = os.path.join(ROOT, "assets", "debug")
    if args.mode == "tree":
        grid, model = build_tree_showcase(seed=args.seed, nx=args.nx, ny=args.ny, tree_height=args.tree_height)
        focus = model.anchor_x, model.anchor_y
        path = os.path.join(out_dir, "test_2x1_dia_tree_section.png")
        export_scene_png(
            grid,
            path,
            focus_cx=focus[0],
            focus_cy=focus[1],
            rotation=args.rotation,
            tree_model=model,
            section_plane="yz",
            section_coord=model.anchor_x,
        )
        print(f"Wrote {path}")
        return 0

    grid = build_meadow_scene(
        seed=args.seed,
        nx=args.nx,
        ny=args.ny,
        scatter_trees=not args.no_trees,
        player=not args.no_player,
        forest_patch=args.forest_patch,
        legacy_trees=args.legacy_trees,
    )
    focus = _default_focus(args.nx, args.ny)
    if args.export_all_rotations:
        for rot in range(4):
            path = os.path.join(out_dir, f"test_2x1_dia_scene_rot{rot}.png")
            export_scene_png(grid, path, focus_cx=focus[0], focus_cy=focus[1], rotation=rot)
            print(f"Wrote {path}")
    else:
        path = os.path.join(out_dir, "test_2x1_dia_meadow.png")
        export_scene_png(grid, path, focus_cx=focus[0], focus_cy=focus[1], rotation=args.rotation)
        print(f"Wrote {path}")
    return 0


def run_interactive(args: argparse.Namespace) -> int:
    pygame.init()
    preset = PRESET_NORMAL
    tree_model = None
    section_plane = "yz"
    section_coord: int | None = None
    top_slice_z = 0
    slice_view: SliceViewMode = "slice"

    if args.mode == "tree":
        grid, tree_model = build_tree_showcase(
            seed=args.seed,
            nx=args.nx,
            ny=args.ny,
            tree_height=args.tree_height,
            species_id=args.species,
            age_years=args.age,
        )
        section_coord = tree_model.anchor_x
        top_slice_z = tree_model.max_z() // 2
    else:
        grid = build_meadow_scene(
            seed=args.seed,
            nx=args.nx,
            ny=args.ny,
            scatter_trees=not args.no_trees,
            player=not args.no_player,
            forest_patch=args.forest_patch,
            legacy_trees=args.legacy_trees,
        )

    renderer = CharGridRenderer(preset=preset)
    sec_renderer = SectionRenderer(preset=preset, panel_w=WINDOW_PX_W // 2)
    fx, fy = _default_focus(args.nx, args.ny)
    if tree_model is not None:
        fx, fy = tree_model.anchor_x, tree_model.anchor_y
    renderer.camera.focus_cx = fx
    renderer.camera.focus_cy = fy
    renderer.camera.rotation = args.rotation % 4

    screen = pygame.display.set_mode((renderer.width, renderer.height))
    pygame.display.set_caption("test_2x1_dia — K view mode | wheel slice | Q/E rotate")

    seed = args.seed
    running = True
    pan_buttons = (1, 2)  # LMB, MMB
    drag_target: str | None = None
    split_section = tree_model is not None
    top_panel_w = WINDOW_PX_W // 2
    section_panel_x0 = top_panel_w
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEWHEEL and tree_model is not None and section_coord is not None:
                if slice_view == "off":
                    continue
                steps = _wheel_steps(ev)
                if not steps:
                    continue
                mx, my = pygame.mouse.get_pos()
                if renderer.point_in_map(mx, my, split_section=split_section):
                    top_slice_z = _clamp_slice_z(top_slice_z + steps, tree_model.max_z())
                elif sec_renderer.point_in_panel(mx, my, panel_x0=section_panel_x0):
                    section_coord = scroll_section_coord(section_plane, section_coord, steps)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button not in pan_buttons:
                    continue
                mx, my = ev.pos
                if renderer.point_in_map(mx, my, split_section=split_section):
                    drag_target = "top"
                elif split_section and sec_renderer.point_in_panel(
                    mx, my, panel_x0=section_panel_x0
                ):
                    drag_target = "section"
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button in pan_buttons:
                    drag_target = None
            elif ev.type == pygame.MOUSEMOTION:
                if not drag_target or not (ev.buttons[0] or ev.buttons[1]):
                    continue
                if drag_target == "top":
                    renderer.camera.pan_pixels(
                        ev.rel[0],
                        ev.rel[1],
                        cell_w=preset.cell_w,
                        cell_h=preset.cell_h,
                    )
                elif drag_target == "section":
                    sec_renderer.pan_pixels(ev.rel[0], ev.rel[1])
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_q:
                    renderer.camera.rotate_ccw()
                elif ev.key == pygame.K_e:
                    renderer.camera.rotate_cw()
                elif ev.key == pygame.K_LEFT:
                    renderer.camera.pan(-1, 0)
                elif ev.key == pygame.K_RIGHT:
                    renderer.camera.pan(1, 0)
                elif ev.key == pygame.K_UP:
                    renderer.camera.pan(0, -1)
                elif ev.key == pygame.K_DOWN:
                    renderer.camera.pan(0, 1)
                elif ev.key in (pygame.K_1, pygame.K_MINUS):
                    preset = PRESET_NORMAL
                    renderer.set_preset(preset)
                    sec_renderer.set_preset(preset)
                elif ev.key in (pygame.K_2, pygame.K_EQUALS):
                    preset = PRESET_COMPACT
                    renderer.set_preset(preset)
                    sec_renderer.set_preset(preset)
                elif ev.key == pygame.K_TAB and tree_model is not None:
                    section_plane = "xz" if section_plane == "yz" else "yz"
                    section_coord = (
                        tree_model.anchor_y if section_plane == "xz" else tree_model.anchor_x
                    )
                    sec_renderer.reset_pan()
                elif ev.key == pygame.K_k and tree_model is not None:
                    slice_view = cycle_slice_view_mode(slice_view)
                elif ev.key == pygame.K_LEFTBRACKET and tree_model is not None and section_coord is not None:
                    section_coord -= 1
                    sec_renderer.reset_pan()
                elif ev.key == pygame.K_RIGHTBRACKET and tree_model is not None and section_coord is not None:
                    section_coord += 1
                    sec_renderer.reset_pan()
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                    if args.mode == "tree":
                        grid, tree_model = build_tree_showcase(
                            seed=seed, nx=args.nx, ny=args.ny, tree_height=args.tree_height
                        )
                        section_coord = tree_model.anchor_x
                        top_slice_z = tree_model.max_z() // 2
                        renderer.camera.focus_cx = tree_model.anchor_x
                        renderer.camera.focus_cy = tree_model.anchor_y
                        sec_renderer.reset_pan()
                    else:
                        grid = build_meadow_scene(
                            seed=seed,
                            nx=args.nx,
                            ny=args.ny,
                            scatter_trees=not args.no_trees,
                            player=not args.no_player,
                            forest_patch=args.forest_patch,
                            legacy_trees=args.legacy_trees,
                        )
                elif ev.key == pygame.K_p:
                    path = os.path.join(ROOT, "assets", "debug", "test_2x1_dia_capture.png")
                    export_scene_png(
                        grid,
                        path,
                        focus_cx=renderer.camera.focus_cx,
                        focus_cy=renderer.camera.focus_cy,
                        rotation=renderer.camera.rotation,
                        preset=preset,
                        tree_model=tree_model,
                        section_plane=section_plane,
                        section_coord=section_coord,
                        top_slice_z=top_slice_z,
                        slice_view=slice_view,
                    )
                    print(f"Wrote {path}")

        hud = renderer.default_hud(grid)
        if args.mode == "tree":
            hud.append(
                f"view={SLICE_VIEW_LABELS[slice_view]} (K) | top Z={top_slice_z} | "
                f"{'proj ' + section_plane.upper() if slice_view == 'off' else f'section {section_plane.upper()} @ {section_coord}'} | "
                f"wheel slice | Tab plane"
            )
        else:
            hud.append("drag / arrows pan | Q/E rotate | 1/2 font | R reseed | P PNG | Esc quit")

        render_kw: dict = {"hud_lines": hud}
        if split_section:
            render_kw["viewport_w"] = top_panel_w
            render_kw["viewport_cx"] = top_panel_w // 2
            if slice_view != "off":
                render_kw["z_cut"] = top_slice_z
                if slice_view == "slice":
                    render_kw["z_cut_solids"] = project_tree_at_z(tree_model, top_slice_z)
                else:
                    render_kw["z_cut_solids"] = project_tree_up_to_z(tree_model, top_slice_z)
                render_kw["section_cut"] = (section_plane, section_coord)
        top = renderer.render(grid, **render_kw)

        if tree_model is not None and section_coord is not None:
            if slice_view == "off":
                if section_plane == "xz":
                    section = project_xz(tree_model)
                    title = "XZ projection"
                else:
                    section = project_yz(tree_model)
                    title = "YZ projection"
            elif section_plane == "xz":
                section = slice_xz(tree_model, section_coord)
                title = f"XZ Y={section_coord}"
            else:
                section = slice_yz(tree_model, section_coord)
                title = f"YZ X={section_coord}"
            section_surf = sec_renderer.render(
                section,
                title=title,
                hud_extra=(
                    f"view={SLICE_VIEW_LABELS[slice_view]} Z={top_slice_z} "
                    f"voxels={len(tree_model.voxels)}"
                ),
                z_cut=top_slice_z if slice_view != "off" else None,
                z_cut_mode=slice_view,
            )
            frame = pygame.Surface((renderer.width, renderer.height))
            blit_split(frame, top, section_surf, top_w=top_panel_w)
            screen.blit(frame, (0, 0))
        else:
            screen.blit(top, (0, 0))
        pygame.display.flip()
        pygame.time.wait(30)

    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="test_2x1_dia char-grid prototype")
    parser.add_argument("--mode", choices=("meadow", "tree"), default="meadow")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--nx", type=int, default=14, help="floor tiles wide")
    parser.add_argument("--ny", type=int, default=12, help="floor tiles tall")
    parser.add_argument("--tree-height", type=int, default=100)
    parser.add_argument("--rotation", type=int, default=0, choices=(0, 1, 2, 3))
    parser.add_argument("--export", action="store_true", help="write PNG and exit")
    parser.add_argument("--export-all-rotations", action="store_true")
    parser.add_argument("--no-trees", action="store_true")
    parser.add_argument("--no-player", action="store_true")
    parser.add_argument("--forest-patch", type=str, default="young_mixed")
    parser.add_argument("--legacy-trees", action="store_true", help="use old stencil tree scatter")
    parser.add_argument("--species", type=str, default="oak")
    parser.add_argument("--age", type=float, default=None)
    args = parser.parse_args()

    if args.mode == "tree":
        args.nx = max(8, args.nx)
        args.ny = max(8, args.ny)
        if args.age is None:
            from src.trees.loader import load_species
            args.age = load_species(args.species).max_age_years * 0.55

    init_paths(ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy" if args.export or args.export_all_rotations else "")

    if args.export or args.export_all_rotations:
        if not os.environ.get("SDL_VIDEODRIVER"):
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        try:
            return run_export(args)
        finally:
            pygame.quit()
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
