"""Volumetric column model for world tiles."""
from __future__ import annotations

from dataclasses import dataclass, field

CLEARANCE_OPEN = 99.0


@dataclass
class Solid:
    z_min: float
    z_max: float
    blocks_movement: bool = False
    blocks_los: bool = False
    stencil_id: str | None = None
    sort_bias: float = 0.0


@dataclass
class Column:
    floor_z: float = 0.0
    floor_ch: str = "."
    floor_stencil_id: str = "grass"
    fg: tuple[int, int, int] = (100, 130, 90)
    bg: tuple[int, int, int] = (30, 45, 30)
    solids: list[Solid] = field(default_factory=list)

    def add_solid(self, solid: Solid) -> None:
        self.solids.append(solid)
        self.solids.sort(key=lambda s: (s.z_min, s.sort_bias))

    def clearance_m(self) -> float:
        blocking = [s.z_min for s in self.solids if s.blocks_movement]
        if not blocking:
            return CLEARANCE_OPEN
        lowest = min(blocking)
        gap = lowest - self.floor_z
        return max(0.0, gap)

    def blocks_los_at(self, eye_z: float = 1.5) -> bool:
        if self.floor_ch in "#░":
            return True
        for s in self.solids:
            if s.blocks_los and s.z_max >= eye_z * 0.3:
                return True
        return False

    def top_display_char(self) -> str:
        """Legacy single-char view for classic render and LOS hints."""
        for s in reversed(self.solids):
            if s.stencil_id and "tree" in s.stencil_id:
                return "T"
            if s.stencil_id and "herb" in s.stencil_id:
                return "o"
            if s.stencil_id and "bush" in s.stencil_id:
                return "o"
        return self.floor_ch
