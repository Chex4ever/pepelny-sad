"""Tree species and forest patch definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

LeafType = Literal["needle", "broadleaf", "none"]
CrownShape = Literal[
    "round", "conical", "columnar", "spread", "flat", "weeping", "umbrella", "layered"
]
GrowthCurve = Literal["sigmoid", "linear"]


@dataclass(frozen=True)
class TreeSpeciesDef:
    id: str
    display_name: str
    leaf_type: LeafType
    height_m: tuple[float, float]
    trunk_radius_m: tuple[float, float]
    crown_shape: CrownShape
    crown_spread: float
    branch_density: float
    branch_angle_deg: float
    trunk_taper: float
    bark_color_id: str
    foliage_color_id: str
    max_age_years: int
    senescence_start: float
    growth_curve: GrowthCurve
    deciduous_needle: bool = False


@dataclass(frozen=True)
class ForestPatchDef:
    id: str
    display_name: str
    species_weights: dict[str, float]
    age_years: dict[str, float]
    density: float
    cluster_radius: int
    dead_ratio: float
    stump_ratio: float
    health_bias: float = 1.0

    @property
    def age_min(self) -> float:
        return float(self.age_years.get("min", 1))

    @property
    def age_max(self) -> float:
        return float(self.age_years.get("max", 50))

    @property
    def age_mean(self) -> float | None:
        m = self.age_years.get("mean")
        return float(m) if m is not None else None
