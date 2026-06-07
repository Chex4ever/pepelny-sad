"""Generate abstract tree morphology from instance spec."""
from __future__ import annotations

import math
import random

from src.trees.instance import TreeInstanceSpec
from src.trees.lifecycle import (
    growth_factor,
    mature_height_m,
    resolve_stage,
    trunk_radius_at_base,
)
from src.trees.loader import load_species
from src.trees.morphology import (
    BranchSegment,
    FoliageBlob,
    TreeLifeStage,
    TreeMorphology,
    TrunkRing,
)
from src.trees.species import CrownShape, TreeSpeciesDef


def _rng(spec: TreeInstanceSpec) -> random.Random:
    return random.Random(spec.seed ^ (spec.wx * 374761393) ^ (spec.wy * 668265263))


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _build_trunk(species: TreeSpeciesDef, height_m: float, base_r: float, taper: float) -> list[TrunkRing]:
    rings: list[TrunkRing] = []
    steps = max(4, int(height_m * 8))
    for i in range(steps + 1):
        t = i / steps
        z = height_m * t
        r = base_r * (1.0 - taper * t)
        rings.append(TrunkRing(z_m=z, radius_m=max(0.04, r)))
    return rings


def _branch_levels(species: TreeSpeciesDef, height_m: float, stage: TreeLifeStage) -> list[float]:
    if stage in (TreeLifeStage.SEEDLING, TreeLifeStage.STUMP, TreeLifeStage.DECAYED):
        return []
    if stage == TreeLifeStage.JUVENILE:
        return [height_m * 0.55]
    if species.crown_shape == "layered":
        return [height_m * t for t in (0.25, 0.45, 0.62, 0.78)]
    if species.crown_shape in ("conical", "columnar"):
        return [height_m * t for t in (0.22, 0.38, 0.52, 0.66, 0.78)]
    return [height_m * t for t in (0.20, 0.35, 0.50, 0.62, 0.72)]


def _branch_count(species: TreeSpeciesDef, rng: random.Random, stage: TreeLifeStage) -> int:
    base = int(3 + species.branch_density * 4)
    if stage == TreeLifeStage.JUVENILE:
        return max(1, base // 2)
    if stage == TreeLifeStage.SENESCENT:
        return max(2, base - 1)
    return base + rng.randint(-1, 2)


def _crown_radius(species: TreeSpeciesDef, height_m: float, z: float, rng: random.Random) -> float:
    rel = z / max(height_m, 0.1)
    spread = species.crown_spread * height_m * 0.35
    shape = species.crown_shape
    if shape == "conical":
        return spread * (1.0 - rel * 0.55)
    if shape == "columnar":
        return spread * 0.45
    if shape == "spread":
        return spread * (0.7 + 0.35 * (1.0 - abs(rel - 0.65)))
    if shape == "umbrella":
        return spread * (0.35 if rel < 0.55 else 1.1)
    if shape == "weeping":
        return spread * (0.5 + rel * 0.5)
    if shape == "flat":
        return spread * 0.9
    if shape == "layered":
        return spread * (0.55 + 0.25 * rng.random())
    return spread * (0.55 + 0.35 * (1.0 - abs(rel - 0.6)))


def _add_branches_and_foliage(
    morph: TreeMorphology,
    species: TreeSpeciesDef,
    rng: random.Random,
    *,
    show_foliage: bool,
) -> None:
    height_m = morph.height_m
    base_r = morph.trunk_segments[-1].radius_m if morph.trunk_segments else 0.2
    levels = _branch_levels(species, height_m, morph.stage)
    angle_base = math.radians(species.branch_angle_deg)
    lean_x, lean_y = morph.lean_x, morph.lean_y
    foliage_kind = "needle_cluster" if species.leaf_type == "needle" else "leaf_cluster"
    senescent_factor = 0.55 if morph.stage == TreeLifeStage.SENESCENT else 1.0

    for z in levels:
        n = _branch_count(species, rng, morph.stage)
        crown_r = _crown_radius(species, height_m, z, rng)
        for i in range(n):
            angle = (2 * math.pi * i / n) + rng.uniform(-0.25, 0.25) + lean_x * 0.1
            length = crown_r * rng.uniform(0.65, 1.15)
            pitch = angle_base * rng.uniform(0.75, 1.15)
            if species.crown_shape == "weeping":
                pitch = math.radians(75 + rng.uniform(-10, 15))
            dx = math.cos(angle) * length * math.cos(pitch)
            dy = math.sin(angle) * length * math.cos(pitch)
            dz = length * math.sin(pitch) * (0.35 if species.crown_shape == "umbrella" else 0.55)
            x0, y0 = lean_x, lean_y
            x1 = x0 + dx
            y1 = y0 + dy
            z1 = min(height_m * 0.98, z + dz)
            br = max(0.04, base_r * 0.35 * (1.0 - z / height_m))
            dead = morph.stage == TreeLifeStage.SENESCENT and rng.random() < 0.25
            kind = "dead_branch" if dead else "branch"
            morph.branches.append(
                BranchSegment(x0, y0, z, x1, y1, z1, br, kind)
            )
            if show_foliage and not dead:
                morph.foliage_clusters.append(
                    FoliageBlob(
                        x=x1, y=y1, z=z1,
                        radius_m=br * rng.uniform(2.5, 4.5) * senescent_factor,
                        density=species.branch_density * senescent_factor,
                        kind=foliage_kind,
                        has_leaves=True,
                    )
                )

    if show_foliage and species.crown_shape in ("round", "spread", "conical", "umbrella", "flat"):
        crown_z = height_m * (0.82 if species.crown_shape != "umbrella" else 0.88)
        cr = _crown_radius(species, height_m, crown_z, rng)
        morph.foliage_clusters.append(
            FoliageBlob(
                x=lean_x, y=lean_y, z=crown_z,
                radius_m=cr * rng.uniform(0.85, 1.1) * senescent_factor,
                density=species.crown_spread * senescent_factor,
                kind=foliage_kind,
                has_leaves=True,
            )
        )


def generate_morphology(spec: TreeInstanceSpec) -> TreeMorphology:
    species = load_species(spec.species_id)
    rng = _rng(spec)
    stage = resolve_stage(
        species,
        spec.age_years,
        spec.health,
        force_stump=spec.force_stump,
        force_dead=spec.force_dead,
    )
    height_m = mature_height_m(species, spec.age_years, stage)
    base_r = trunk_radius_at_base(species, spec.age_years, stage)
    lean_x = rng.uniform(-0.15, 0.15) * growth_factor(species, spec.age_years)
    lean_y = rng.uniform(-0.15, 0.15) * growth_factor(species, spec.age_years)

    morph = TreeMorphology(
        species_id=spec.species_id,
        stage=stage,
        age_years=spec.age_years,
        height_m=height_m,
        health=spec.health,
        lean_x=lean_x,
        lean_y=lean_y,
        seed=spec.seed,
    )

    if stage in (TreeLifeStage.STUMP, TreeLifeStage.DECAYED):
        morph.trunk_segments = _build_trunk(species, height_m, base_r, species.trunk_taper * 0.3)
        return morph

    morph.trunk_segments = _build_trunk(species, height_m, base_r, species.trunk_taper)
    show_foliage = stage not in (TreeLifeStage.DEAD_STANDING, TreeLifeStage.DECAYED)
    if show_foliage and species.leaf_type == "needle" and species.deciduous_needle:
        if spec.age_years > species.max_age_years * 0.4:
            show_foliage = rng.random() > 0.1

    if stage != TreeLifeStage.SEEDLING:
        _add_branches_and_foliage(morph, species, rng, show_foliage=show_foliage)

    return morph
