"""Inspect world tiles for level editor."""
from __future__ import annotations

from typing import Any

from src.world.editor.editable_world import EditableWorld


def inspect_cell(world: EditableWorld, wx: int, wy: int) -> dict[str, Any]:
    chunk, lx, ly = world.chunk_for_world(wx, wy)
    col = chunk.to_column(lx, ly)
    anchors = [
        {
            "structure_id": a.structure_id,
            "wx": a.wx,
            "wy": a.wy,
            "params": a.params,
        }
        for a in chunk.structure_anchors
        if a.wx == wx and a.wy == wy
    ]
    return {
        "wx": wx,
        "wy": wy,
        "chunk": (chunk.cx, chunk.cy),
        "local": (lx, ly),
        "char": col.floor_ch,
        "stencil": col.floor_stencil_id,
        "fg": col.fg,
        "bg": col.bg,
        "solids": [
            {
                "stencil": s.stencil_id,
                "z_min": s.z_min,
                "z_max": s.z_max,
            }
            for s in col.solids
        ],
        "anchors": anchors,
    }


def inspect_diag_tile(world: EditableWorld, wx: int, wy: int) -> dict[str, Any]:
    """One diag floor tile (3×2 stamp) — single template from world column."""
    b = world.bounds
    info = inspect_cell(world, wx, wy)
    info["tile_tx"] = wx - b.wx0
    info["tile_ty"] = wy - b.wy0
    info["template_id"] = info["stencil"]
    return info
