"""Parametric trees 3-10m with multi-cell canopy."""
from __future__ import annotations

import random

from src.world.column import Solid
from src.world.structures import StructureAnchor

GLOBAL_HEIGHT_MIN = 3.0
GLOBAL_HEIGHT_MAX = 10.0


def _tile_rng(seed: int, wx: int, wy: int) -> random.Random:
    return random.Random(seed ^ (wx * 374761393) ^ (wy * 668265263))


def roll_tree_params(biome: dict, seed: int, wx: int, wy: int) -> dict:
    rng = _tile_rng(seed, wx, wy)
    hmin, hmax = biome.get("tree_height_m", [4.0, 8.0])
    height_m = rng.uniform(float(hmin), float(hmax))
    height_m = max(GLOBAL_HEIGHT_MIN, min(GLOBAL_HEIGHT_MAX, height_m))
    return {
        "height_m": round(height_m, 2),
        "trunk_ratio": rng.uniform(0.35, 0.45),
        "canopy_radius": rng.randint(1, 3 if height_m > 6 else 2),
        "lean": rng.choice([-1, 0, 0, 0, 1]),
        "variant": rng.randint(0, 5),
        "thick_trunk": height_m > 5.5,
    }


def build_tree_solids(params: dict) -> list[tuple[int, int, Solid]]:
    height_m = params["height_m"]
    trunk_z = height_m * params["trunk_ratio"]
    variant = params["variant"]
    radius = params["canopy_radius"]
    lean = params["lean"]
    trunk_stencil = "tree_trunk_thick" if params.get("thick_trunk") else "tree_trunk_slim"
    canopy_stencil = f"tree_canopy_v{variant}_h{int(height_m)}_r{radius}"
    solids: list[tuple[int, int, Solid]] = [
        (
            0,
            0,
            Solid(0.0, trunk_z, blocks_movement=True, blocks_los=True, stencil_id=trunk_stencil),
        ),
        (
            lean,
            0,
            Solid(trunk_z * 0.85, height_m, blocks_movement=False, blocks_los=True, stencil_id=canopy_stencil),
        ),
    ]
    if radius >= 2:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            solids.append(
                (
                    dx + lean,
                    dy,
                    Solid(
                        trunk_z * 0.9,
                        height_m * 0.95,
                        blocks_movement=False,
                        stencil_id=canopy_stencil,
                    ),
                )
            )
    return solids


def tree_anchor(wx: int, wy: int, biome: dict, seed: int) -> StructureAnchor:
    params = roll_tree_params(biome, seed, wx, wy)
    return StructureAnchor("tree", wx, wy, params)


def solids_at_world(anchor: StructureAnchor, wx: int, wy: int) -> list[Solid]:
    if anchor.structure_id != "tree" or not anchor.params:
        return []
    out: list[Solid] = []
    for dx, dy, solid in build_tree_solids(anchor.params):
        if anchor.wx + dx == wx and anchor.wy + dy == wy:
            out.append(solid)
    return out


def apply_tree_solids(world_map, anchor: StructureAnchor) -> None:
    """Bake tree volumes into chunk cell_solids (avoids per-frame anchor scans)."""
    if not anchor.params:
        return
    for dx, dy, solid in build_tree_solids(anchor.params):
        tw, th = anchor.wx + dx, anchor.wy + dy
        cx, cy, lx, ly = world_map.world_to_chunk(tw, th)
        world_map._ensure_chunk(cx, cy)
        world_map.chunks[(cx, cy)].add_solid(lx, ly, solid)


def place_tree_anchor(chunk, wx: int, wy: int, biome: dict, seed: int, world_map=None) -> StructureAnchor:
    anchor = tree_anchor(wx, wy, biome, seed)
    chunk.structure_anchors.append(anchor)
    if world_map is not None:
        apply_tree_solids(world_map, anchor)
    return anchor
