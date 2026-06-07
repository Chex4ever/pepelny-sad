"""Abstract tree geometry (graphics-agnostic)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

BranchKind = Literal[
    "trunk", "branch", "twig", "dead_branch", "bark_only"
]
FoliageKind = Literal["leaf_cluster", "needle_cluster", "none"]


class TreeLifeStage(str, Enum):
    SEEDLING = "seedling"
    JUVENILE = "juvenile"
    MATURE = "mature"
    SENESCENT = "senescent"
    DEAD_STANDING = "dead_standing"
    STUMP = "stump"
    DECAYED = "decayed"


@dataclass(frozen=True)
class TrunkRing:
    z_m: float
    radius_m: float


@dataclass(frozen=True)
class BranchSegment:
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float
    radius_m: float
    kind: BranchKind


@dataclass(frozen=True)
class FoliageBlob:
    x: float
    y: float
    z: float
    radius_m: float
    density: float
    kind: FoliageKind
    has_leaves: bool


@dataclass
class TreeMorphology:
    species_id: str
    stage: TreeLifeStage
    age_years: float
    height_m: float
    health: float
    trunk_segments: list[TrunkRing] = field(default_factory=list)
    branches: list[BranchSegment] = field(default_factory=list)
    foliage_clusters: list[FoliageBlob] = field(default_factory=list)
    lean_x: float = 0.0
    lean_y: float = 0.0
    seed: int = 0

    def has_foliage(self) -> bool:
        return any(f.has_leaves for f in self.foliage_clusters)
