"""Tree instance specs and rolling from forest patches."""
from __future__ import annotations

import random
from dataclasses import dataclass

from src.trees.loader import load_forest_patch, load_species_catalog
from src.trees.species import ForestPatchDef


@dataclass(frozen=True)
class TreeInstanceSpec:
    species_id: str
    seed: int
    age_years: float
    health: float = 1.0
    wx: int = 0
    wy: int = 0
    force_stump: bool = False
    force_dead: bool = False

    def to_dict(self) -> dict:
        return {
            "species_id": self.species_id,
            "seed": self.seed,
            "age_years": self.age_years,
            "health": self.health,
            "wx": self.wx,
            "wy": self.wy,
            "force_stump": self.force_stump,
            "force_dead": self.force_dead,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TreeInstanceSpec:
        return cls(
            species_id=d["species_id"],
            seed=int(d["seed"]),
            age_years=float(d["age_years"]),
            health=float(d.get("health", 1.0)),
            wx=int(d.get("wx", 0)),
            wy=int(d.get("wy", 0)),
            force_stump=bool(d.get("force_stump", False)),
            force_dead=bool(d.get("force_dead", False)),
        )


def _tile_rng(world_seed: int, wx: int, wy: int) -> random.Random:
    return random.Random(world_seed ^ (wx * 374761393) ^ (wy * 668265263))


def _pick_species(rng: random.Random, patch: ForestPatchDef) -> str:
    catalog = load_species_catalog()
    weights = [(sid, w) for sid, w in patch.species_weights.items() if w > 0 and sid in catalog]
    if not weights:
        return next(iter(catalog))
    total = sum(w for _, w in weights)
    roll = rng.random() * total
    acc = 0.0
    for sid, w in weights:
        acc += w
        if roll <= acc:
            return sid
    return weights[-1][0]


def _roll_age(rng: random.Random, patch: ForestPatchDef) -> float:
    if patch.age_mean is not None:
        span = patch.age_max - patch.age_min
        age = rng.gauss(patch.age_mean, span * 0.2)
        return max(patch.age_min, min(patch.age_max, age))
    return rng.uniform(patch.age_min, patch.age_max)


def roll_tree_instance(
    patch: ForestPatchDef,
    *,
    world_seed: int,
    wx: int,
    wy: int,
) -> TreeInstanceSpec:
    rng = _tile_rng(world_seed, wx, wy)
    species_id = _pick_species(rng, patch)
    age = _roll_age(rng, patch)
    health = max(0.0, min(1.0, patch.health_bias + rng.uniform(-0.15, 0.15)))

    force_dead = False
    force_stump = False
    if patch.dead_ratio >= 1.0:
        force_dead = True
    elif rng.random() < patch.dead_ratio:
        force_dead = True
    if force_dead and rng.random() < patch.stump_ratio:
        force_stump = True
    elif not force_dead and rng.random() < patch.stump_ratio:
        force_stump = True

    instance_seed = world_seed ^ (wx * 911382323) ^ (wy * 340573321) ^ hash(species_id)

    return TreeInstanceSpec(
        species_id=species_id,
        seed=instance_seed & 0x7FFFFFFF,
        age_years=age,
        health=0.0 if force_dead else health,
        wx=wx,
        wy=wy,
        force_stump=force_stump,
        force_dead=force_dead and not force_stump,
    )


def roll_tree_instance_by_patch_id(
    patch_id: str,
    *,
    world_seed: int,
    wx: int,
    wy: int,
) -> TreeInstanceSpec:
    return roll_tree_instance(load_forest_patch(patch_id), world_seed=world_seed, wx=wx, wy=wy)
