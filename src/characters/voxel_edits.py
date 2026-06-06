"""Manual voxel edit layer for character editor."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel


@dataclass
class VoxelEditLayer:
    additions: dict[tuple[int, int, int], str] = field(default_factory=dict)
    removals: set[tuple[int, int, int]] = field(default_factory=set)

    def clear(self) -> None:
        self.additions.clear()
        self.removals.clear()

    def add(self, x: int, y: int, z: int, kind: str) -> None:
        pos = (x, y, z)
        self.removals.discard(pos)
        self.additions[pos] = kind

    def remove(self, x: int, y: int, z: int) -> None:
        pos = (x, y, z)
        self.additions.pop(pos, None)
        self.removals.add(pos)

    def to_dict(self) -> dict[str, Any]:
        return {
            "additions": {f"{x},{y},{z}": k for (x, y, z), k in self.additions.items()},
            "removals": [f"{x},{y},{z}" for x, y, z in sorted(self.removals)],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VoxelEditLayer:
        layer = cls()
        for key, kind in data.get("additions", {}).items():
            parts = [int(p) for p in str(key).split(",")]
            if len(parts) == 3:
                layer.additions[(parts[0], parts[1], parts[2])] = str(kind)
        for key in data.get("removals", []):
            parts = [int(p) for p in str(key).split(",")]
            if len(parts) == 3:
                layer.removals.add((parts[0], parts[1], parts[2]))
        return layer


def apply_edits(
    voxels: dict[tuple[int, int, int], str],
    edits: VoxelEditLayer | None,
) -> dict[tuple[int, int, int], str]:
    if not edits:
        return dict(voxels)
    out = dict(voxels)
    for pos in edits.removals:
        out.pop(pos, None)
    for pos, kind in edits.additions.items():
        out[pos] = kind
    return out


def apply_edits_to_model(model: TreeVoxelModel, edits: VoxelEditLayer | None) -> TreeVoxelModel:
    from dataclasses import replace

    merged = apply_edits(model.voxels, edits)
    return replace(model, voxels=merged)


def save_voxel_edits(path: str, edits: VoxelEditLayer) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(edits.to_dict(), f, indent=2, ensure_ascii=False)


def load_voxel_edits(path: str) -> VoxelEditLayer:
    with open(path, encoding="utf-8") as f:
        return VoxelEditLayer.from_dict(json.load(f))
