"""Place multi-cell structures into world columns."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from src import constants
from src.world.column import Solid

if TYPE_CHECKING:
    from src.world.world_map import WorldMap


@dataclass
class StructureAnchor:
    structure_id: str
    wx: int
    wy: int
    params: dict | None = None


def _data_path() -> str:
    import os

    return os.path.join(constants.DATA_DIR, "structures.json")


@lru_cache(maxsize=1)
def load_structures() -> dict:
    with open(_data_path(), encoding="utf-8") as f:
        return json.load(f)


def _solids_from_template(structure_id: str, height_scale: float = 1.0) -> list[tuple[int, int, Solid]]:
    tpl = load_structures().get(structure_id, {})
    out: list[tuple[int, int, Solid]] = []
    for part in tpl.get("parts", []):
        solid = Solid(
            z_min=part["z_min"] * height_scale,
            z_max=part["z_max"] * height_scale,
            blocks_movement=part.get("blocks_movement", False),
            blocks_los=part.get("blocks_los", False),
            stencil_id=part.get("stencil"),
        )
        out.append((part.get("dx", 0), part.get("dy", 0), solid))
    return out


def place_structure(world_map: "WorldMap", structure_id: str, wx: int, wy: int, layer: str = "surface") -> None:
    cx, cy, _, _ = world_map.world_to_chunk(wx, wy)
    world_map._ensure_chunk(cx, cy)
    chunk = world_map.chunks[(cx, cy)]
    chunk.structure_anchors.append(StructureAnchor(structure_id, wx, wy))
    for dx, dy, solid in _solids_from_template(structure_id):
        tw, th = wx + dx, wy + dy
        tcx, tcy, tlx, tly = world_map.world_to_chunk(tw, th)
        if (tcx, tcy) not in world_map.chunks:
            continue
        world_map.chunks[(tcx, tcy)].add_solid(tlx, tly, solid)
