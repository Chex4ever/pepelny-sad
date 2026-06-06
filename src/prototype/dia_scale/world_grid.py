"""Sparse world-fixed char grid for dia_scale prototype."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FloorCell:
    ch: str
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]


@dataclass
class GridSolid:
    cx: int
    cy: int
    z_min: float
    z_max: float
    stencil_id: str
    fg: tuple[int, int, int]
    bg: tuple[int, int, int]
    ch: str = "@"
    kind: str = "solid"


@dataclass
class GridEntity:
    entity_id: str
    feet_cx: int
    feet_cy: int
    cells: list[tuple[int, int, str, tuple[int, int, int], tuple[int, int, int]]]
    z_sort: float = 0.5


@dataclass
class WorldGrid:
    floor: dict[tuple[int, int], FloorCell] = field(default_factory=dict)
    solids: list[GridSolid] = field(default_factory=list)
    entities: list[GridEntity] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def set_floor(self, cx: int, cy: int, cell: FloorCell) -> None:
        self.floor[(cx, cy)] = cell

    def has_floor(self, cx: int, cy: int) -> bool:
        return (cx, cy) in self.floor

    def add_solid(self, solid: GridSolid) -> None:
        self.solids.append(solid)

    def add_entity(self, entity: GridEntity) -> None:
        self.entities.append(entity)

    def floor_bounds(self) -> tuple[int, int, int, int] | None:
        if not self.floor:
            return None
        xs = [k[0] for k in self.floor]
        ys = [k[1] for k in self.floor]
        return min(xs), min(ys), max(xs), max(ys)

    def all_draw_cells(self) -> list[tuple[float, int, int, str, tuple, tuple, str]]:
        """Flat draw list: (sort_key, cx, cy, ch, fg, bg, layer)."""
        items: list[tuple[float, int, int, str, tuple, tuple, str]] = []
        for (cx, cy), fc in self.floor.items():
            items.append((float(cy), cx, cy, fc.ch, fc.fg, fc.bg, "floor"))
        for s in self.solids:
            items.append((float(s.cy) + s.z_max * 0.01, s.cx, s.cy, s.ch, s.fg, s.bg, s.kind))
        for ent in self.entities:
            for cx, cy, ch, fg, bg in ent.cells:
                items.append((float(cy) + ent.z_sort, cx, cy, ch, fg, bg, ent.entity_id))
        items.sort(key=lambda t: (t[0], t[2], t[1]))
        return items
