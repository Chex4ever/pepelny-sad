#!/usr/bin/env python3
"""Generator / viewer for all surface biomes — same GPU iso path as the game.

Run from repo root:
  python scripts/biome_viewer.py
  python scripts/biome_viewer.py --render iso
  python scripts/biome_viewer.py --export-all
  python scripts/biome_viewer.py --export meadow --seed 4242

Default render: PEPELNY_RENDER=gpu (GpuIsoRenderer + footprint fill, like overworld).
Use --render iso only to compare CPU glyph path.

Controls (window):
  ←/→     prev/next biome (forced mode)
  M       toggle forced biome vs climate sampling
  H       toggle hole overlay on saved PNG (analysis is CPU geometry)
  T       trees on/off
  +/-     patch size
  R       new seed
  G       auto-cycle all biomes (same GPU view)
  W/S     shift climate sample origin (climate mode)
  E       save PNG to assets/debug/
  Esc     quit
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import (
    CELL_H,
    CELL_W,
    CHUNK_SIZE,
    ISO_ORIGIN_X,
    ISO_ORIGIN_Y,
    ISO_STEP_X,
    ISO_STEP_Y,
    SCREEN_H,
    SCREEN_W,
    init_paths,
)
from src.data.art_loader import load_biomes
from src.render.iso_projector import IsoProjector
from src.render.screen_buffer import ScreenBuffer
from src.tools.iso_preview import (
    OverworldPreview,
    analyze_queue_footprint,
    build_surface_draw_queue,
    preview_mode_label,
    render_queue_cpu,
    resolve_preview_mode,
)
from src.world.biome_blend import sample_climate
from src.world.chunk import Chunk
from src.world.surface_detail import maybe_grass_overlay, pick_floor_stencil
from src.world.surface_gen import sample_surface_into_chunk
from src.world.world_fields import init_world_fields

BUF_W, BUF_H = SCREEN_W, SCREEN_H


@dataclass
class PatchStats:
    biome_id: str
    seed: int
    wx0: int
    wy0: int
    w: int
    h: int
    forced: bool
    trees: bool
    floor_variants: Counter = field(default_factory=Counter)
    internal_holes: int = 0
    unstamped_holes: int = 0
    covered_cells: int = 0
    drawn_cells: int = 0
    render_path: str = "gpu"

    def to_dict(self) -> dict[str, Any]:
        return {
            "biome_id": self.biome_id,
            "seed": self.seed,
            "wx0": self.wx0,
            "wy0": self.wy0,
            "w": self.w,
            "h": self.h,
            "forced": self.forced,
            "trees": self.trees,
            "floor_variants": dict(self.floor_variants),
            "internal_holes": self.internal_holes,
            "unstamped_holes": self.unstamped_holes,
            "covered_cells": self.covered_cells,
            "drawn_cells": self.drawn_cells,
            "render_path": self.render_path,
        }


def _fill_forced_tile(
    chunk: Chunk,
    lx: int,
    ly: int,
    wx: int,
    wy: int,
    biome_id: str,
    seed: int,
    *,
    trees: bool,
) -> None:
    biome = dict(load_biomes()[biome_id])
    if not trees:
        biome["tree_chance"] = 0
        biome["bush_chance"] = 0
    floor = biome["floor"]
    fg = tuple(biome["fg"])
    bg = tuple(biome["bg"])
    stencil_id = pick_floor_stencil(biome_id, wx, wy, seed)
    chunk.set_floor(lx, ly, floor, fg=fg, bg=bg, stencil_id=stencil_id)
    chunk.biome_counts[biome_id] += 1
    overlay = maybe_grass_overlay(biome, wx, wy, seed)
    if overlay:
        chunk.add_solid(lx, ly, overlay)
    rng = random.Random(seed ^ (wx << 8) ^ wy)
    if trees and biome.get("tree_chance", 0) > 0 and rng.random() < biome["tree_chance"]:
        from src.world.tree_generator import place_tree_anchor

        place_tree_anchor(chunk, wx, wy, biome, seed, world_map=None)
    elif rng.random() < biome.get("herb_chance", 0):
        from src.world.column import Solid

        chunk.add_solid(lx, ly, Solid(0.05, 0.15, blocks_movement=False, stencil_id="herb"))


def generate_patch(
    wx0: int,
    wy0: int,
    w: int,
    h: int,
    seed: int,
    *,
    forced_biome: str | None,
    trees: bool,
) -> Chunk:
    if w > CHUNK_SIZE or h > CHUNK_SIZE:
        raise ValueError(f"patch max {CHUNK_SIZE}x{CHUNK_SIZE}")
    init_world_fields(seed)
    chunk = Chunk(0, 0)
    rng = random.Random(seed ^ 0xA5A5)
    tree_mask: set[tuple[int, int]] = set()
    for dy in range(h):
        for dx in range(w):
            wx, wy = wx0 + dx, wy0 + dy
            lx, ly = dx, dy
            if forced_biome:
                _fill_forced_tile(
                    chunk, lx, ly, wx, wy, forced_biome, seed, trees=trees
                )
            else:
                sample_surface_into_chunk(
                    chunk, lx, ly, wx, wy, seed, rng, tree_mask, world_map=None
                )
    if not trees:
        _strip_trees_from_chunk(chunk)
    elif chunk.structure_anchors:
        from src.world.tree_generator import bake_tree_anchors_on_chunk

        bake_tree_anchors_on_chunk(chunk)
    return chunk


def _strip_trees_from_chunk(chunk: Chunk) -> None:
    skip = ("tree", "bush", "trunk", "canopy")
    for i in range(CHUNK_SIZE * CHUNK_SIZE):
        solids = chunk.cell_solids[i]
        chunk.cell_solids[i] = [
            s
            for s in solids
            if not any(part in (s.stencil_id or "") for part in skip)
        ]
    chunk.structure_anchors.clear()


def prepare_patch(
    wx0: int,
    wy0: int,
    w: int,
    h: int,
    seed: int,
    biome_id: str,
    *,
    forced: bool,
    trees: bool,
    render_mode: str | None = None,
) -> tuple[Chunk, list[tuple], PatchStats, list[tuple[int, int]]]:
    chunk = generate_patch(
        wx0,
        wy0,
        w,
        h,
        seed,
        forced_biome=biome_id if forced else None,
        trees=trees,
    )
    focus_wx = wx0 + w // 2
    focus_wy = wy0 + h // 2
    queue = build_surface_draw_queue(chunk, wx0, wy0, w, h)
    holes, _, covered = analyze_queue_footprint(
        queue, focus_wx=focus_wx, focus_wy=focus_wy
    )
    buf = render_queue_cpu(queue, focus_wx=focus_wx, focus_wy=focus_wy)
    drawn: set[tuple[int, int]] = set()
    for y in range(BUF_H):
        for x in range(BUF_W):
            if buf.chars[buf._idx(x, y)] != " ":
                drawn.add((x, y))
    unstamped = [c for c in holes if c not in drawn]
    stats = PatchStats(
        biome_id=biome_id if forced else "climate",
        seed=seed,
        wx0=wx0,
        wy0=wy0,
        w=w,
        h=h,
        forced=forced,
        trees=trees,
        render_path=render_mode
        if render_mode in ("gpu", "iso")
        else resolve_preview_mode(render_mode),
    )
    for dy in range(h):
        for dx in range(w):
            stats.floor_variants[chunk.floor_stencils[chunk.idx(dx, dy)]] += 1
    stats.covered_cells = len(covered)
    stats.internal_holes = len(holes)
    stats.unstamped_holes = len(unstamped)
    stats.drawn_cells = len(drawn)
    return chunk, queue, stats, holes + unstamped


def draw_hole_overlay(
    surf: pygame.Surface,
    holes: list[tuple[int, int]],
) -> None:
    for gx, gy in holes:
        pygame.draw.rect(
            surf, (255, 50, 50), (gx * CELL_W, gy * CELL_H, CELL_W, CELL_H), 1
        )


def export_png(
    path: str,
    surf: pygame.Surface,
    holes: list[tuple[int, int]],
    *,
    show_holes: bool,
) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if show_holes:
        draw_hole_overlay(surf, holes)
    pygame.image.save(surf, path)


def run_export_all(out_dir: str, seed: int, size: int, render_mode: str | None) -> int:
    init_paths(ROOT)
    pygame.init()
    preview = OverworldPreview(render_mode)
    biomes = load_biomes()
    report: dict[str, Any] = {
        "seed": seed,
        "size": size,
        "render_path": preview.mode,
        "biomes": {},
    }
    wx0, wy0 = 100, 100
    worst = ("", 0)
    for bid in sorted(biomes.keys()):
        _chunk, queue, stats, holes = prepare_patch(
            wx0, wy0, size, size, seed, bid, forced=True, trees=False, render_mode=preview.mode
        )
        focus_wx, focus_wy = wx0 + size // 2, wy0 + size // 2
        surf = preview.capture(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        fname = f"biome_{bid}_s{seed}_{size}x{size}_{preview.mode}.png"
        fpath = os.path.join(out_dir, fname)
        export_png(fpath, surf, holes, show_holes=True)
        report["biomes"][bid] = stats.to_dict()
        total_holes = stats.internal_holes + stats.unstamped_holes
        if total_holes > worst[1]:
            worst = (bid, total_holes)
        sparse = stats.floor_variants.get("grass_sparse", 0)
        total = max(1, sum(stats.floor_variants.values()))
        report["biomes"][bid]["grass_sparse_pct"] = round(100.0 * sparse / total, 1)
    report["worst_holes"] = {"biome": worst[0], "count": worst[1]}
    report_path = os.path.join(out_dir, f"report_s{seed}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(biomes)} PNGs + {report_path}")
    print(f"Worst internal coverage: {worst[0]} ({worst[1]} holes)")
    for bid, data in report["biomes"].items():
        print(
            f"  {bid}: holes={data['internal_holes']}+{data['unstamped_holes']} "
            f"sparse={data.get('grass_sparse_pct', 0)}% variants={data['floor_variants']}"
        )
    preview.release()
    pygame.quit()
    return 0 if worst[1] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Biome iso viewer")
    parser.add_argument("--export-all", action="store_true")
    parser.add_argument("--export", metavar="BIOME")
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--size", type=int, default=14)
    parser.add_argument(
        "--out-dir",
        default=os.path.join(ROOT, "assets", "debug", "biomes"),
    )
    parser.add_argument(
        "--render",
        choices=("gpu", "iso"),
        default=None,
        help="gpu = as in game (default); iso = CPU glyph debug",
    )
    args = parser.parse_args()

    if args.export_all:
        return run_export_all(args.out_dir, args.seed, args.size, args.render)

    if args.export:
        init_paths(ROOT)
        pygame.init()
        preview = OverworldPreview(args.render)
        _c, queue, stats, holes = prepare_patch(
            0, 0, args.size, args.size, args.seed, args.export, forced=True, trees=False, render_mode=preview.mode
        )
        path = os.path.join(
            args.out_dir, f"biome_{args.export}_s{args.seed}_{preview.mode}.png"
        )
        surf = preview.capture(queue, focus_wx=args.size // 2, focus_wy=args.size // 2)
        export_png(path, surf, holes, show_holes=True)
        print(json.dumps(stats.to_dict(), ensure_ascii=False, indent=2))
        preview.release()
        pygame.quit()
        return 0

    init_paths(ROOT)
    pygame.init()
    preview = OverworldPreview(args.render)
    pygame.display.set_caption(f"Биомы — {preview.mode_label}")
    screen = pygame.display.get_surface()
    small = pygame.font.SysFont("consolas", 13)

    biomes = sorted(load_biomes().keys())
    biome_idx = 0
    seed = args.seed
    patch = args.size
    wx0, wy0 = 80, 80
    forced = True
    trees = False
    show_holes = True
    gallery = False
    frame = 0

    running = True
    while running:
        frame += 1
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    biome_idx = (biome_idx - 1) % len(biomes)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    biome_idx = (biome_idx + 1) % len(biomes)
                elif ev.key == pygame.K_m:
                    forced = not forced
                elif ev.key == pygame.K_h:
                    show_holes = not show_holes
                elif ev.key == pygame.K_t:
                    trees = not trees
                elif ev.key == pygame.K_g:
                    gallery = not gallery
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    patch = min(CHUNK_SIZE, patch + 2)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    patch = max(6, patch - 2)
                elif ev.key == pygame.K_w:
                    wy0 -= 8
                elif ev.key == pygame.K_s:
                    wy0 += 8
                elif ev.key == pygame.K_e:
                    os.makedirs(os.path.join(ROOT, "assets", "debug"), exist_ok=True)
                    bid = biomes[biome_idx] if forced else "climate"
                    _c, queue, stats, holes = prepare_patch(
                        wx0,
                        wy0,
                        patch,
                        patch,
                        seed,
                        biomes[biome_idx],
                        forced=forced,
                        trees=trees,
                        render_mode=preview.mode,
                    )
                    path = os.path.join(
                        ROOT,
                        "assets",
                        "debug",
                        f"biome_{bid}_s{seed}_{patch}_{preview.mode}.png",
                    )
                    surf = preview.capture(
                        queue,
                        focus_wx=wx0 + patch // 2,
                        focus_wy=wy0 + patch // 2,
                    )
                    export_png(path, surf, holes, show_holes=show_holes)
                    print("saved", path, stats.to_dict())

        if gallery:
            biome_idx = (frame // 45) % len(biomes)
        bid = biomes[biome_idx]
        mode = f"forced:{bid}" if forced else f"climate @ ({wx0},{wy0})"
        if gallery:
            mode = f"[GALLERY cycle] {mode}"
        _c, queue, stats, holes = prepare_patch(
            wx0,
            wy0,
            patch,
            patch,
            seed,
            bid,
            forced=forced,
            trees=trees,
            render_mode=preview.mode,
        )
        focus_wx, focus_wy = wx0 + patch // 2, wy0 + patch // 2
        hud = [
            f"{preview.mode_label}",
            f"{mode} seed={seed} {patch}x{patch} trees={trees}",
            f"geom holes {stats.internal_holes}+{stats.unstamped_holes} (cpu) floor={dict(stats.floor_variants)}",
            f"{load_biomes()[bid].get('floor_variants')}",
            "E PNG  G auto-cycle biomes  H holes on export  Esc quit",
        ]
        preview.present(queue, focus_wx=focus_wx, focus_wy=focus_wy, hud_lines=hud)
        pygame.time.wait(40)

    preview.release()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
