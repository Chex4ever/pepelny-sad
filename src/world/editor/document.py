"""EditorDocument JSON save/load for surface maps."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.world.chunk import Chunk
from src.world.column import Solid
from src.world.structures import StructureAnchor


MAP_VERSION = 1


@dataclass
class MapBounds:
    wx0: int = 0
    wy0: int = 0
    width: int = 32
    height: int = 32


@dataclass
class EditorDocument:
    version: int = MAP_VERSION
    seed: int = 0
    bounds: MapBounds = field(default_factory=MapBounds)
    chunks: dict[tuple[int, int], Chunk] = field(default_factory=dict)

    def chunk_at(self, cx: int, cy: int) -> Chunk:
        if (cx, cy) not in self.chunks:
            self.chunks[(cx, cy)] = Chunk(cx, cy)
        return self.chunks[(cx, cy)]

    def world_to_chunk(self, wx: int, wy: int) -> tuple[int, int, int, int]:
        from src.constants import CHUNK_SIZE

        cx = wx // CHUNK_SIZE if wx >= 0 else (wx + 1) // CHUNK_SIZE - 1
        cy = wy // CHUNK_SIZE if wy >= 0 else (wy + 1) // CHUNK_SIZE - 1
        lx = wx - cx * CHUNK_SIZE
        ly = wy - cy * CHUNK_SIZE
        return cx, cy, lx, ly

    def get_column(self, wx: int, wy: int):
        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        return self.chunk_at(cx, cy).to_column(lx, ly)

    def to_dict(self) -> dict[str, Any]:
        chunk_list = []
        for (cx, cy), chunk in sorted(self.chunks.items()):
            n = len(chunk.tiles)
            from src.constants import CHUNK_SIZE

            solids_ser = []
            for i, solids in enumerate(chunk.cell_solids):
                if not solids:
                    continue
                ly = i // CHUNK_SIZE
                lx = i % CHUNK_SIZE
                solids_ser.append({
                    "lx": lx,
                    "ly": ly,
                    "solids": [_solid_to_dict(s) for s in solids],
                })
            anchors = [
                {
                    "structure_id": a.structure_id,
                    "wx": a.wx,
                    "wy": a.wy,
                    "params": a.params,
                }
                for a in chunk.structure_anchors
            ]
            chunk_list.append({
                "cx": cx,
                "cy": cy,
                "tiles": list(chunk.tiles),
                "fg": [list(c) for c in chunk.fg],
                "bg": [list(c) for c in chunk.bg],
                "floor_stencils": list(chunk.floor_stencils),
                "cell_solids": solids_ser,
                "structure_anchors": anchors,
            })
        return {
            "version": self.version,
            "seed": self.seed,
            "bounds": {
                "wx0": self.bounds.wx0,
                "wy0": self.bounds.wy0,
                "width": self.bounds.width,
                "height": self.bounds.height,
            },
            "chunks": chunk_list,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EditorDocument:
        from src.constants import CHUNK_SIZE

        b = data.get("bounds", {})
        doc = cls(
            version=int(data.get("version", MAP_VERSION)),
            seed=int(data.get("seed", 0)),
            bounds=MapBounds(
                wx0=int(b.get("wx0", 0)),
                wy0=int(b.get("wy0", 0)),
                width=int(b.get("width", 32)),
                height=int(b.get("height", 32)),
            ),
        )
        for raw in data.get("chunks", []):
            cx, cy = int(raw["cx"]), int(raw["cy"])
            chunk = Chunk(cx, cy)
            chunk.tiles = list(raw.get("tiles", chunk.tiles))
            chunk.fg = [tuple(c) for c in raw.get("fg", chunk.fg)]
            chunk.bg = [tuple(c) for c in raw.get("bg", chunk.bg)]
            chunk.floor_stencils = list(raw.get("floor_stencils", chunk.floor_stencils))
            chunk.cell_solids = [[] for _ in range(CHUNK_SIZE * CHUNK_SIZE)]
            for entry in raw.get("cell_solids", []):
                lx, ly = int(entry["lx"]), int(entry["ly"])
                chunk.cell_solids[chunk.idx(lx, ly)] = [
                    _solid_from_dict(s) for s in entry.get("solids", [])
                ]
            chunk.structure_anchors = [
                StructureAnchor(
                    structure_id=str(a["structure_id"]),
                    wx=int(a["wx"]),
                    wy=int(a["wy"]),
                    params=a.get("params"),
                )
                for a in raw.get("structure_anchors", [])
            ]
            doc.chunks[(cx, cy)] = chunk
        return doc


def _solid_to_dict(s: Solid) -> dict[str, Any]:
    return {
        "z_min": s.z_min,
        "z_max": s.z_max,
        "blocks_movement": s.blocks_movement,
        "blocks_los": s.blocks_los,
        "stencil_id": s.stencil_id,
        "sort_bias": s.sort_bias,
    }


def _solid_from_dict(d: dict[str, Any]) -> Solid:
    return Solid(
        z_min=float(d["z_min"]),
        z_max=float(d["z_max"]),
        blocks_movement=bool(d.get("blocks_movement", False)),
        blocks_los=bool(d.get("blocks_los", False)),
        stencil_id=d.get("stencil_id"),
        sort_bias=float(d.get("sort_bias", 0.0)),
    )


def save_map(path: str | Path, doc: EditorDocument) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc.to_dict(), indent=2), encoding="utf-8")


def load_map(path: str | Path) -> EditorDocument:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return EditorDocument.from_dict(data)
