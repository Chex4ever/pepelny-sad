"""Character race definitions."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LimbRatios:
    arm: float
    leg: float
    neck: float


@dataclass(frozen=True)
class AgeThresholds:
    child_max: float
    young_max: float
    adult_max: float


@dataclass(frozen=True)
class PaletteSlots:
    skin: tuple[str, ...]
    hair: tuple[str, ...]
    eye: tuple[str, ...]


@dataclass(frozen=True)
class FeatureRule:
    id: str
    seed_threshold: float = 0.0


@dataclass(frozen=True)
class RaceDef:
    id: str
    display_name: str
    height_m: tuple[float, float]
    shoulder_scale: float
    limb_scale: float
    head_scale: float
    torso_scale: float
    limb_ratios: LimbRatios
    ear_type: str
    ear_length_m: float
    jaw_scale: float
    cheek_hollow: float
    max_age_years: int
    grey_hair_age: float
    palette_slots: PaletteSlots
    hair_styles: tuple[str, ...]
    allow_beard: bool
    beard_styles: tuple[str, ...]
    age_thresholds: AgeThresholds
    feature_rules: tuple[str | FeatureRule, ...] = field(default_factory=tuple)
    body_opacity: float = 1.0
    posture_rigid: bool = False
