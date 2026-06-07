"""Tree life stage from age and health."""
from __future__ import annotations

from src.trees.morphology import TreeLifeStage
from src.trees.species import TreeSpeciesDef


def resolve_stage(
    species: TreeSpeciesDef,
    age_years: float,
    health: float,
    *,
    force_stump: bool = False,
    force_dead: bool = False,
) -> TreeLifeStage:
    if force_stump:
        return TreeLifeStage.STUMP
    if force_dead or health <= 0.0:
        return TreeLifeStage.DEAD_STANDING
    max_age = float(species.max_age_years)
    if age_years >= max_age:
        return TreeLifeStage.DEAD_STANDING
    if age_years <= 0.01:
        return TreeLifeStage.SEEDLING
    ratio = age_years / max(max_age, 1.0)
    if ratio < 0.05:
        return TreeLifeStage.SEEDLING
    if ratio < 0.25:
        return TreeLifeStage.JUVENILE
    if ratio >= species.senescence_start:
        if health < 0.35:
            return TreeLifeStage.DEAD_STANDING
        return TreeLifeStage.SENESCENT
    return TreeLifeStage.MATURE


def growth_factor(species: TreeSpeciesDef, age_years: float) -> float:
    """0..1 maturity for height/radius scaling."""
    max_age = float(species.max_age_years)
    t = max(0.0, min(1.0, age_years / max(max_age, 1.0)))
    if species.growth_curve == "linear":
        return t
    # sigmoid centered ~0.35
    import math
    return 1.0 / (1.0 + math.exp(-8.0 * (t - 0.35)))


def mature_height_m(species: TreeSpeciesDef, age_years: float, stage: TreeLifeStage) -> float:
    hmin, hmax = species.height_m
    g = growth_factor(species, age_years)
    height = hmin + (hmax - hmin) * g
    if stage == TreeLifeStage.SEEDLING:
        return max(0.15, height * 0.08)
    if stage == TreeLifeStage.JUVENILE:
        return max(0.4, height * 0.45)
    if stage == TreeLifeStage.STUMP:
        return max(0.1, (hmin + (hmax - hmin) * 0.9) * 0.12)
    if stage == TreeLifeStage.DECAYED:
        return max(0.05, (hmin + (hmax - hmin) * 0.5) * 0.06)
    if stage == TreeLifeStage.SENESCENT:
        return height * 0.92
    if stage == TreeLifeStage.DEAD_STANDING:
        return height * 0.88
    return height


def trunk_radius_at_base(species: TreeSpeciesDef, age_years: float, stage: TreeLifeStage) -> float:
    rmin, rmax = species.trunk_radius_m
    g = growth_factor(species, age_years)
    radius = rmin + (rmax - rmin) * g
    if stage in (TreeLifeStage.SEEDLING, TreeLifeStage.JUVENILE):
        radius *= 0.5 + 0.5 * growth_factor(species, age_years)
    if stage == TreeLifeStage.STUMP:
        radius *= 1.1
    return radius
