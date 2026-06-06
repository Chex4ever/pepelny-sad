"""Abstract character body geometry."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

BuildKind = Literal["lean", "average", "heavy"]


class LifeStage(str, Enum):
    CHILD = "child"
    YOUNG = "young"
    ADULT = "adult"
    ELDER = "elder"


@dataclass(frozen=True)
class TraitRoll:
    height_bias: float
    build: BuildKind
    face_width: float
    jaw: float
    nose: float
    brow: float
    skin_palette_idx: int
    hair_palette_idx: int
    eye_palette_idx: int
    hair_style_idx: int
    beard_style_idx: int
    asymmetry: float
    feature_roll: float


@dataclass(frozen=True)
class BodySegment:
    kind: str
    length_m: float
    radius_m: float
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    taper: float = 0.85


@dataclass(frozen=True)
class AnchorPoint:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class BodyProportions:
    """Anthropometric radii / half-widths in metres."""
    shoulder_hw: float
    hip_hw: float
    chest_depth: float
    thigh_r: float
    calf_r: float
    upper_arm_r: float
    forearm_r: float
    head_r: float
    neck_r: float
    foot_r: float
    leg_spread: float
    head_h: float
    neck_h: float
    torso_h: float
    pelvis_h: float
    thigh_h: float
    calf_h: float
    foot_h: float


@dataclass
class CharacterMorphology:
    race_id: str
    life_stage: LifeStage
    age_years: float
    height_m: float
    segments: list[BodySegment] = field(default_factory=list)
    anchors: dict[str, AnchorPoint] = field(default_factory=dict)
    joints: dict[str, AnchorPoint] = field(default_factory=dict)
    proportions: BodyProportions | None = None
    traits: TraitRoll | None = None
    palette: dict[str, str] = field(default_factory=dict)
    features: list[str] = field(default_factory=list)
    seed: int = 0
    sex: str = "neutral"
    hair_style_id: str = "bald"
    beard_style_id: str | None = None

    def has_feature(self, name: str) -> bool:
        return name in self.features
