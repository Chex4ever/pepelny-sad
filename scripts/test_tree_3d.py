#!/usr/bin/env python3
"""Full-window 3D voxel tree viewer (spin with RMB).

Run:
  python scripts/test_tree_3d.py
  python scripts/test_tree_3d.py --species birch --age 25
  python scripts/test_tree_3d.py --seed 42 --export
"""
from __future__ import annotations

import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import init_paths
from src.prototype.dia_scale.display_scale import PRESET_COMPACT, PRESET_NORMAL, WINDOW_PX_H, WINDOW_PX_W
from src.prototype.dia_scale.scene import build_tree_showcase
from src.prototype.dia_scale.slice_view import SLICE_VIEW_LABELS, SliceViewMode, cycle_slice_view_mode
from src.prototype.dia_scale.voxel_3d_renderer import Voxel3DRenderer
from src.trees.loader import load_species_catalog


def _wheel_steps(ev: pygame.event.Event) -> int:
    if getattr(ev, "precise_y", 0):
        return int(round(ev.precise_y))
    y = ev.y
    if y == 0:
        return 0
    return y // 120 or (1 if y > 0 else -1)


def _clamp_slice_z(z: int, z_max: int) -> int:
    return max(0, min(z_max, z))


def _orbit_label(renderer: Voxel3DRenderer) -> str:
    o = renderer.orbit
    return (
        f"yaw={math.degrees(o.yaw):.0f} pitch={math.degrees(o.pitch):.0f} "
        f"roll={math.degrees(o.roll):.0f} zoom={o.zoom:.1f}"
    )


def _species_list() -> list[str]:
    return sorted(load_species_catalog().keys())


def _next_species(current: str, delta: int) -> str:
    ids = _species_list()
    i = ids.index(current) if current in ids else 0
    return ids[(i + delta) % len(ids)]


def _rebuild_tree(args, seed: int, species_id: str, age_years: float):
    return build_tree_showcase(
        seed=seed,
        nx=args.nx,
        ny=args.ny,
        tree_height=args.tree_height,
        species_id=species_id,
        age_years=age_years,
    )


def run_export(args: argparse.Namespace) -> int:
    grid, model = _rebuild_tree(args, args.seed, args.species, args.age)
    pygame.init()
    renderer = Voxel3DRenderer(preset=PRESET_NORMAL)
    surf = renderer.render(
        model,
        title=f"{args.species} age={args.age:.0f}",
        hud_lines=[f"seed={args.seed}"],
        slice_view="off",
    )
    out_dir = os.path.join(ROOT, "assets", "debug")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "test_tree_3d.png")
    pygame.image.save(surf, path)
    print(f"Wrote {path}")
    return 0


def run_interactive(args: argparse.Namespace) -> int:
    pygame.init()
    preset = PRESET_NORMAL
    species_id = args.species
    age_years = args.age
    grid, tree_model = _rebuild_tree(args, args.seed, species_id, age_years)
    species = load_species_catalog()[species_id]

    renderer = Voxel3DRenderer(preset=preset)
    section_plane = "yz"
    section_coord = tree_model.anchor_x
    top_slice_z = tree_model.max_z() // 2
    slice_view: SliceViewMode = "off"

    screen = pygame.display.set_mode((WINDOW_PX_W, WINDOW_PX_H))
    pygame.display.set_caption("test_tree_3d — Tab species | [/] age | RMB orbit")

    seed = args.seed
    running = True
    drag_mode: str | None = None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEWHEEL:
                steps = _wheel_steps(ev)
                if not steps:
                    continue
                if slice_view == "off":
                    renderer.orbit.zoom_wheel(steps)
                else:
                    top_slice_z = _clamp_slice_z(top_slice_z + steps, tree_model.max_z())
                    if slice_view == "slice":
                        section_coord += steps
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:
                    drag_mode = "orbit"
                elif ev.button in (1, 2):
                    drag_mode = "pan"
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button in (1, 2, 3):
                    drag_mode = None
            elif ev.type == pygame.MOUSEMOTION:
                if not drag_mode:
                    continue
                if drag_mode == "orbit" and ev.buttons[2]:
                    renderer.orbit.rotate_drag(ev.rel[0], ev.rel[1])
                elif drag_mode == "pan" and (ev.buttons[0] or ev.buttons[1]):
                    renderer.orbit.pan_pixels(ev.rel[0], ev.rel[1])
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_1, pygame.K_MINUS):
                    preset = PRESET_NORMAL
                    renderer.set_preset(preset)
                elif ev.key in (pygame.K_2, pygame.K_EQUALS):
                    preset = PRESET_COMPACT
                    renderer.set_preset(preset)
                elif ev.key == pygame.K_k:
                    slice_view = cycle_slice_view_mode(slice_view)
                elif ev.key == pygame.K_TAB:
                    species_id = _next_species(species_id, 1)
                    species = load_species_catalog()[species_id]
                    grid, tree_model = _rebuild_tree(args, seed, species_id, age_years)
                    section_coord = tree_model.anchor_x
                    top_slice_z = tree_model.max_z() // 2
                elif ev.key == pygame.K_LEFTBRACKET:
                    age_years = max(0.0, age_years - max(1.0, species.max_age_years * 0.05))
                    grid, tree_model = _rebuild_tree(args, seed, species_id, age_years)
                    top_slice_z = min(top_slice_z, tree_model.max_z())
                elif ev.key == pygame.K_RIGHTBRACKET:
                    age_years = min(float(species.max_age_years), age_years + max(1.0, species.max_age_years * 0.05))
                    grid, tree_model = _rebuild_tree(args, seed, species_id, age_years)
                    top_slice_z = tree_model.max_z() // 2
                elif ev.key == pygame.K_HOME:
                    renderer.reset_view()
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                    grid, tree_model = _rebuild_tree(args, seed, species_id, age_years)
                    section_coord = tree_model.anchor_x
                    top_slice_z = tree_model.max_z() // 2
                    renderer.reset_view()
                elif ev.key == pygame.K_p:
                    path = os.path.join(ROOT, "assets", "debug", "test_tree_3d_capture.png")
                    surf = renderer.render(
                        tree_model,
                        title="capture",
                        slice_view=slice_view,
                        section_plane=section_plane,
                        section_coord=section_coord,
                        top_slice_z=top_slice_z,
                    )
                    pygame.image.save(surf, path)
                    print(f"Wrote {path}")

        mode_txt = (
            f"proj {section_plane.upper()}"
            if slice_view == "off"
            else f"{SLICE_VIEW_LABELS[slice_view]} Z={top_slice_z} {section_plane.upper()}@{section_coord}"
        )
        hud = [
            f"{species.display_name} ({species_id}) age={age_years:.0f}/{species.max_age_years}y seed={seed}",
            f"view={SLICE_VIEW_LABELS[slice_view]} (K) | {mode_txt} | Tab next species | [/] age",
            f"{_orbit_label(renderer)} | RMB orbit | LMB/MMB pan | wheel zoom",
        ]
        title = f"3D {species.display_name}"
        if slice_view != "off":
            title += f" [{SLICE_VIEW_LABELS[slice_view]}]"

        surf = renderer.render(
            tree_model,
            title=title,
            hud_lines=hud,
            slice_view=slice_view,
            section_plane=section_plane,
            section_coord=section_coord,
            top_slice_z=top_slice_z,
        )
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        pygame.time.wait(30)

    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="3D voxel tree viewer")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--nx", type=int, default=8)
    parser.add_argument("--ny", type=int, default=8)
    parser.add_argument("--tree-height", type=int, default=100)
    parser.add_argument("--species", type=str, default="oak")
    parser.add_argument("--age", type=float, default=None, help="tree age in years")
    parser.add_argument("--export", action="store_true", help="write PNG and exit")
    args = parser.parse_args()
    args.nx = max(8, args.nx)
    args.ny = max(8, args.ny)
    if args.age is None:
        from src.trees.loader import load_species
        args.age = load_species(args.species).max_age_years * 0.55

    init_paths(ROOT)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy" if args.export else "")

    if args.export:
        if not os.environ.get("SDL_VIDEODRIVER"):
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        try:
            return run_export(args)
        finally:
            pygame.quit()
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
