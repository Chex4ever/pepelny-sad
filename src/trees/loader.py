"""Load species and forest patch data from JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.trees.species import ForestPatchDef, TreeSpeciesDef

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _parse_species(sid: str, raw: dict) -> TreeSpeciesDef:
    h = raw["height_m"]
    tr = raw["trunk_radius_m"]
    return TreeSpeciesDef(
        id=sid,
        display_name=raw.get("display_name", sid),
        leaf_type=raw["leaf_type"],
        height_m=(float(h[0]), float(h[1])),
        trunk_radius_m=(float(tr[0]), float(tr[1])),
        crown_shape=raw["crown_shape"],
        crown_spread=float(raw.get("crown_spread", 0.5)),
        branch_density=float(raw.get("branch_density", 0.6)),
        branch_angle_deg=float(raw.get("branch_angle_deg", 45)),
        trunk_taper=float(raw.get("trunk_taper", 0.6)),
        bark_color_id=raw.get("bark_color_id", "bark_generic"),
        foliage_color_id=raw.get("foliage_color_id", "foliage_spring_green"),
        max_age_years=int(raw.get("max_age_years", 100)),
        senescence_start=float(raw.get("senescence_start", 0.75)),
        growth_curve=raw.get("growth_curve", "sigmoid"),
        deciduous_needle=bool(raw.get("deciduous_needle", False)),
    )


def _parse_patch(pid: str, raw: dict) -> ForestPatchDef:
    weights = {k: float(v) for k, v in raw["species_weights"].items()}
    return ForestPatchDef(
        id=pid,
        display_name=raw.get("display_name", pid),
        species_weights=weights,
        age_years={k: float(v) for k, v in raw["age_years"].items()},
        density=float(raw.get("density", 0.2)),
        cluster_radius=int(raw.get("cluster_radius", 5)),
        dead_ratio=float(raw.get("dead_ratio", 0.0)),
        stump_ratio=float(raw.get("stump_ratio", 0.0)),
        health_bias=float(raw.get("health_bias", 1.0)),
    )


@lru_cache(maxsize=1)
def load_species_catalog() -> dict[str, TreeSpeciesDef]:
    path = _DATA_DIR / "species.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {sid: _parse_species(sid, data) for sid, data in raw.items()}


@lru_cache(maxsize=1)
def load_forest_patches() -> dict[str, ForestPatchDef]:
    path = _DATA_DIR / "forest_patches.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {pid: _parse_patch(pid, data) for pid, data in raw.items()}


@lru_cache(maxsize=1)
def load_palette() -> dict[str, dict[str, list[int]]]:
    path = _DATA_DIR / "palette.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_species(species_id: str) -> TreeSpeciesDef:
    catalog = load_species_catalog()
    if species_id not in catalog:
        raise KeyError(f"unknown species: {species_id}")
    return catalog[species_id]


def load_forest_patch(patch_id: str) -> ForestPatchDef:
    patches = load_forest_patches()
    if patch_id not in patches:
        raise KeyError(f"unknown forest patch: {patch_id}")
    return patches[patch_id]
