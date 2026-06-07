"""Load character data from JSON."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.characters.race import AgeThresholds, FeatureRule, LimbRatios, PaletteSlots, RaceDef

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _parse_feature_rule(raw) -> str | FeatureRule:
    if isinstance(raw, str):
        return raw
    return FeatureRule(id=raw["id"], seed_threshold=float(raw.get("seed_threshold", 0.0)))


def _parse_race(rid: str, raw: dict) -> RaceDef:
    lr = raw["limb_ratios"]
    ps = raw["palette_slots"]
    at = raw["age_thresholds"]
    h = raw["height_m"]
    return RaceDef(
        id=rid,
        display_name=raw.get("display_name", rid),
        height_m=(float(h[0]), float(h[1])),
        shoulder_scale=float(raw.get("shoulder_scale", 1.0)),
        limb_scale=float(raw.get("limb_scale", 1.0)),
        head_scale=float(raw.get("head_scale", 1.0)),
        torso_scale=float(raw.get("torso_scale", 1.0)),
        limb_ratios=LimbRatios(
            arm=float(lr["arm"]),
            leg=float(lr["leg"]),
            neck=float(lr["neck"]),
        ),
        ear_type=raw.get("ear_type", "none"),
        ear_length_m=float(raw.get("ear_length_m", 0.0)),
        jaw_scale=float(raw.get("jaw_scale", 1.0)),
        cheek_hollow=float(raw.get("cheek_hollow", 0.0)),
        max_age_years=int(raw.get("max_age_years", 90)),
        grey_hair_age=float(raw.get("grey_hair_age", 50)),
        palette_slots=PaletteSlots(
            skin=tuple(ps["skin"]),
            hair=tuple(ps["hair"]),
            eye=tuple(ps["eye"]),
        ),
        hair_styles=tuple(raw.get("hair_styles", [])),
        allow_beard=bool(raw.get("allow_beard", False)),
        beard_styles=tuple(raw.get("beard_styles", [])),
        age_thresholds=AgeThresholds(
            child_max=float(at["child_max"]),
            young_max=float(at["young_max"]),
            adult_max=float(at["adult_max"]),
        ),
        feature_rules=tuple(_parse_feature_rule(r) for r in raw.get("feature_rules", [])),
        body_opacity=float(raw.get("body_opacity", 1.0)),
        posture_rigid=bool(raw.get("posture_rigid", False)),
    )


@lru_cache(maxsize=1)
def load_races_catalog() -> dict[str, RaceDef]:
    path = _DATA_DIR / "races.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {rid: _parse_race(rid, data) for rid, data in raw.items()}


@lru_cache(maxsize=1)
def load_palette() -> dict[str, dict[str, list[int]]]:
    path = _DATA_DIR / "palette.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_hair_styles() -> dict:
    path = _DATA_DIR / "hair_styles.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_equipment_visuals() -> dict:
    path = _DATA_DIR / "equipment_visuals.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_poses() -> dict:
    path = _DATA_DIR / "poses.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_race(race_id: str) -> RaceDef:
    catalog = load_races_catalog()
    if race_id not in catalog:
        raise KeyError(f"unknown race: {race_id}")
    return catalog[race_id]
