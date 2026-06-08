"""Procedural fill tools for level editor (write into EditableWorld)."""
from __future__ import annotations

import random
from typing import Iterable

from src.data.art_loader import load_biomes
from src.world.column import Solid
from src.world.editor.editable_world import EditableWorld
from src.world.editor.tools import EditorTools
from src.world.surface_detail import maybe_grass_overlay, pick_floor_stencil
from src.world.tree_generator import bake_tree_anchors_on_chunk, place_tree_anchor
from src.world.world_fields import init_world_fields


def _fill_forced_tile(
    chunk,
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
        place_tree_anchor(chunk, wx, wy, biome, seed, world_map=None)
    elif rng.random() < biome.get("herb_chance", 0):
        chunk.add_solid(lx, ly, Solid(0.05, 0.15, blocks_movement=False, stencil_id="herb"))


def fill_biome(
    world: EditableWorld,
    biome_id: str,
    *,
    trees: bool = False,
) -> None:
    """Fill document bounds with a single biome (climate sampling off)."""
    init_world_fields(world.seed)
    b = world.bounds
    for cx, cy in list(world.doc.chunks.keys()):
        chunk = world.doc.chunk_at(cx, cy)
        chunk.biome_counts.clear()
        chunk.structure_anchors = [
            a
            for a in chunk.structure_anchors
            if not (b.wx0 <= a.wx < b.wx0 + b.width and b.wy0 <= a.wy < b.wy0 + b.height)
        ]

    for wx, wy in world.iter_local_cells():
        chunk, lx, ly = world.chunk_for_world(wx, wy)
        chunk.set_cell_solids(lx, ly, [])
        _fill_forced_tile(chunk, lx, ly, wx, wy, biome_id, world.seed, trees=trees)

    if trees:
        for chunk, _wx0, _wy0, _w, _h in world.world_scene_chunks():
            bake_tree_anchors_on_chunk(chunk)


def _cells_along_polyline(points: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    pts = list(points)
    if len(pts) < 2:
        return set(pts)
    out: set[tuple[int, int]] = set()
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for s in range(steps + 1):
            t = s / steps
            out.add((round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)))
    return out


def paint_road(
    world: EditableWorld,
    points: list[tuple[int, int]],
    *,
    width: int = 2,
    stencil_id: str = "road",
) -> None:
    """Corridor along polyline in world tiles."""
    tools = EditorTools(world)
    core = _cells_along_polyline(points)
    cells: set[tuple[int, int]] = set()
    for wx, wy in core:
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                cells.add((wx + dx, wy + dy))
    b = world.bounds
    for wx, wy in cells:
        if not (b.wx0 <= wx < b.wx0 + b.width and b.wy0 <= wy < b.wy0 + b.height):
            continue
        tools.paint_floor(wx, wy, ch="=", stencil_id=stencil_id)


def make_clearing(
    world: EditableWorld,
    wx0: int,
    wy0: int,
    w: int,
    h: int,
    *,
    stencil_id: str = "meadow",
) -> None:
    """Strip solids and set open meadow floor in a rectangle."""
    tools = EditorTools(world)
    for dy in range(h):
        for dx in range(w):
            wx, wy = wx0 + dx, wy0 + dy
            b = world.bounds
            if not (b.wx0 <= wx < b.wx0 + b.width and b.wy0 <= wy < b.wy0 + b.height):
                continue
            tools.erase_cell(wx, wy)
            tools.paint_floor(wx, wy, stencil_id=stencil_id)


def scatter_trees(
    world: EditableWorld,
    *,
    biome_id: str = "meadow",
    density: float = 0.04,
) -> None:
    """Random tree placement across bounds."""
    tools = EditorTools(world)
    rng = random.Random(world.seed ^ 0x7EED)
    for wx, wy in world.iter_local_cells():
        if rng.random() < density:
            tools.place_tree(wx, wy, biome_id=biome_id)


def scatter_bushes_in_bounds(
    world: EditableWorld,
    *,
    density: float = 0.06,
    structure_id: str = "bush_low",
) -> None:
    b = world.bounds
    EditorTools(world).scatter_bushes(
        b.wx0, b.wy0, b.width, b.height, density=density, structure_id=structure_id
    )
