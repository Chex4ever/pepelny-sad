"""Age → life stage."""
from __future__ import annotations

from src.characters.morphology import LifeStage
from src.characters.race import RaceDef


def resolve_life_stage(age_years: float, race: RaceDef) -> LifeStage:
    t = race.age_thresholds
    if age_years <= t.child_max:
        return LifeStage.CHILD
    if age_years <= t.young_max:
        return LifeStage.YOUNG
    if age_years <= t.adult_max:
        return LifeStage.ADULT
    return LifeStage.ELDER


_STAGE_HEIGHT: dict[LifeStage, tuple[float, float]] = {
    LifeStage.CHILD: (0.62, 0.72),
    LifeStage.YOUNG: (0.88, 0.95),
    LifeStage.ADULT: (1.0, 1.0),
    LifeStage.ELDER: (0.93, 0.97),
}


def stage_height_multiplier(stage: LifeStage, height_bias: float) -> float:
    lo, hi = _STAGE_HEIGHT[stage]
    return lo + (hi - lo) * height_bias


def stage_head_scale(stage: LifeStage, base: float) -> float:
    if stage == LifeStage.CHILD:
        return base * 1.35
    if stage == LifeStage.YOUNG:
        return base * 1.08
    if stage == LifeStage.ELDER:
        return base * 1.02
    return base


def stage_limb_multiplier(stage: LifeStage) -> float:
    if stage == LifeStage.CHILD:
        return 0.85
    return 1.0


def stage_posture_slouch(stage: LifeStage, rigid: bool) -> float:
    if rigid:
        return 0.0
    if stage == LifeStage.ELDER:
        return -0.03
    return 0.0
