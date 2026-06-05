#!/usr/bin/env python3
"""GPU/iso viewer for game objects (sprites + tile stencils) — same path as overworld.

Run from repo root:
  python scripts/object_viewer.py
  python scripts/object_viewer.py --object player
  python scripts/object_viewer.py --object player --no-floor
  python scripts/object_viewer.py --export player --seed 1

Default render: PEPELNY_RENDER=gpu (GpuIsoRenderer + per-glyph atlas, like the game).

Controls (window):
  ←/→     prev/next object
  F       toggle meadow floor under object
  B       cycle floor biome (when floor on)
  +/-     patch size
  R       new floor seed
  E       save PNG to assets/debug/
  Esc     quit
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import CHUNK_SIZE, init_paths
from src.data.art_loader import load_biomes
from src.render.tile_stencil import load_sprite, load_tile_stencil
from src.tools.iso_preview import (
    OverworldPreview,
    build_object_preview_queue,
    list_object_preview_ids,
)

# Re-use biome patch generator for optional floor.
from scripts.biome_viewer import generate_patch


def _object_label(object_id: str) -> str:
    if object_id.startswith("sprite:"):
        return object_id.split(":", 1)[1]
    return object_id


def _glyph_summary(object_id: str) -> str:
    if object_id.startswith("sprite:"):
        st = load_sprite(object_id.split(":", 1)[1])
    else:
        st = load_tile_stencil(object_id)
    chars = sorted({g.ch for g in st.glyphs})
    return f"glyphs={len(st.glyphs)} chars={''.join(chars)}"


def prepare_object_scene(
    object_id: str,
    *,
    wx0: int,
    wy0: int,
    patch: int,
    seed: int,
    floor_biome: str,
    show_floor: bool,
) -> tuple[list[tuple], dict]:
    cx = wx0 + patch // 2
    cy = wy0 + patch // 2
    chunk = (
        generate_patch(wx0, wy0, patch, patch, seed, forced_biome=floor_biome, trees=False)
        if show_floor
        else None
    )
    queue = build_object_preview_queue(
        object_id,
        wx=cx,
        wy=cy,
        floor_chunk=chunk,
        wx0=wx0,
        wy0=wy0,
        w=patch,
        h=patch,
    )
    meta = {
        "object_id": object_id,
        "label": _object_label(object_id),
        "glyphs": _glyph_summary(object_id),
        "wx0": wx0,
        "wy0": wy0,
        "patch": patch,
        "seed": seed,
        "floor_biome": floor_biome,
        "show_floor": show_floor,
        "anchor_wx": cx,
        "anchor_wy": cy,
    }
    return queue, meta


def run_export(
    object_id: str,
    *,
    out_dir: str,
    seed: int,
    patch: int,
    floor_biome: str,
    show_floor: bool,
    render_mode: str | None,
) -> int:
    init_paths(ROOT)
    pygame.init()
    preview = OverworldPreview(render_mode)
    queue, meta = prepare_object_scene(
        object_id,
        wx0=0,
        wy0=0,
        patch=patch,
        seed=seed,
        floor_biome=floor_biome,
        show_floor=show_floor,
    )
    focus_wx, focus_wy = meta["anchor_wx"], meta["anchor_wy"]
    surf = preview.capture(queue, focus_wx=focus_wx, focus_wy=focus_wy)
    os.makedirs(out_dir, exist_ok=True)
    floor_tag = floor_biome if show_floor else "plain"
    fname = f"object_{meta['label']}_s{seed}_{floor_tag}_{preview.mode}.png"
    path = os.path.join(out_dir, fname)
    pygame.image.save(surf, path)
    meta["render_path"] = preview.mode
    meta["png"] = path
    report = os.path.join(out_dir, f"object_{meta['label']}_s{seed}.json")
    with open(report, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    preview.release()
    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Object / sprite iso viewer (GPU)")
    parser.add_argument(
        "--object",
        default="sprite:player",
        help="sprite:player or stencil id (tree, herb, …)",
    )
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--size", type=int, default=12)
    parser.add_argument("--floor-biome", default="meadow")
    parser.add_argument("--no-floor", action="store_true")
    parser.add_argument(
        "--export",
        metavar="OBJECT",
        help="Export PNG and exit (defaults to --object if omitted)",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(ROOT, "assets", "debug", "objects"),
    )
    parser.add_argument(
        "--render",
        choices=("gpu", "iso"),
        default=None,
        help="gpu = as in game; iso = CPU glyph compare",
    )
    args = parser.parse_args()

    if args.export:
        export_id = args.export
        eid = export_id if export_id.startswith("sprite:") else f"sprite:{export_id}"
        return run_export(
            eid,
            out_dir=args.out_dir,
            seed=args.seed,
            patch=args.size,
            floor_biome=args.floor_biome,
            show_floor=not args.no_floor,
            render_mode=args.render,
        )

    init_paths(ROOT)
    objects = list_object_preview_ids()
    object_id = args.object
    if not object_id.startswith("sprite:") and object_id not in objects:
        object_id = f"sprite:{object_id}"
    if object_id not in objects:
        print(f"Unknown object {object_id!r}; choose from: {objects}")
        return 1
    pygame.init()
    preview = OverworldPreview(args.render)
    pygame.display.set_caption(f"Объекты — {preview.mode_label}")

    biomes = sorted(load_biomes().keys())
    biome_idx = biomes.index(args.floor_biome) if args.floor_biome in biomes else 0
    obj_idx = max(0, objects.index(object_id))
    seed = args.seed
    patch = args.size
    wx0, wy0 = 80, 80
    show_floor = not args.no_floor

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    obj_idx = (obj_idx - 1) % len(objects)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    obj_idx = (obj_idx + 1) % len(objects)
                elif ev.key == pygame.K_f:
                    show_floor = not show_floor
                elif ev.key == pygame.K_b:
                    biome_idx = (biome_idx + 1) % len(biomes)
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    patch = min(CHUNK_SIZE, patch + 2)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    patch = max(6, patch - 2)
                elif ev.key == pygame.K_e:
                    oid = objects[obj_idx]
                    queue, meta = prepare_object_scene(
                        oid,
                        wx0=wx0,
                        wy0=wy0,
                        patch=patch,
                        seed=seed,
                        floor_biome=biomes[biome_idx],
                        show_floor=show_floor,
                    )
                    os.makedirs(os.path.join(ROOT, "assets", "debug", "objects"), exist_ok=True)
                    surf = preview.capture(
                        queue,
                        focus_wx=meta["anchor_wx"],
                        focus_wy=meta["anchor_wy"],
                    )
                    floor_tag = biomes[biome_idx] if show_floor else "plain"
                    path = os.path.join(
                        ROOT,
                        "assets",
                        "debug",
                        "objects",
                        f"object_{meta['label']}_s{seed}_{floor_tag}_{preview.mode}.png",
                    )
                    pygame.image.save(surf, path)
                    print("saved", path)

        oid = objects[obj_idx]
        floor_biome = biomes[biome_idx]
        queue, meta = prepare_object_scene(
            oid,
            wx0=wx0,
            wy0=wy0,
            patch=patch,
            seed=seed,
            floor_biome=floor_biome,
            show_floor=show_floor,
        )
        hud = [
            f"{preview.mode_label}",
            f"{oid}  {_glyph_summary(oid)}",
            f"floor={floor_biome if show_floor else 'off'} seed={seed} {patch}x{patch}",
            "←/→ object  F floor  B biome  E PNG  Esc quit",
        ]
        preview.present(
            queue,
            focus_wx=meta["anchor_wx"],
            focus_wy=meta["anchor_wy"],
            hud_lines=hud,
        )
        pygame.time.wait(40)

    preview.release()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
