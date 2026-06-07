"""Equipment attachment resolution."""
from __future__ import annotations

from dataclasses import dataclass

from src.characters.loader import load_equipment_visuals


@dataclass(frozen=True)
class EquipmentAttachment:
    item_id: str
    slot: str
    anchor: str
    anchor_secondary: str | None
    voxel_template: str
    kind: str
    palette: str
    occlusion_mask: tuple[str, ...]


def resolve_attachments(equipment: dict[str, str | None]) -> list[EquipmentAttachment]:
    data = load_equipment_visuals()
    items = data.get("items", {})
    out: list[EquipmentAttachment] = []
    for _slot, item_id in equipment.items():
        if not item_id or item_id not in items:
            continue
        raw = items[item_id]
        out.append(
            EquipmentAttachment(
                item_id=item_id,
                slot=raw["slot"],
                anchor=raw["anchor"],
                anchor_secondary=raw.get("anchor_secondary"),
                voxel_template=raw["voxel_template"],
                kind=raw.get("kind", "equipment"),
                palette=raw.get("palette", "metal_steel"),
                occlusion_mask=tuple(raw.get("occlusion_mask", [])),
            )
        )
    return out
