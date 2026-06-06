"""Seed-driven trait rolls."""
from __future__ import annotations

import random

from src.characters.morphology import BuildKind, TraitRoll
from src.characters.race import FeatureRule, RaceDef
from src.characters.spec import CharacterSpec


def _race_hash(race_id: str) -> int:
    h = 0
    for ch in race_id:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def _rng(spec: CharacterSpec) -> random.Random:
    return random.Random(spec.seed ^ _race_hash(spec.race_id))


def roll_traits(spec: CharacterSpec, race: RaceDef, tuning=None) -> TraitRoll:
    from src.characters.tuning import TuningState

    if tuning and isinstance(tuning, TuningState):
        builds: tuple[BuildKind, ...] = ("lean", "average", "heavy")
        kw: dict = {}
        for name in (
            "height_bias", "face_width", "jaw", "nose", "brow", "asymmetry", "feature_roll",
        ):
            path = f"traits.{name}"
            if tuning.is_locked(path):
                kw[name] = float(tuning.get(path))
        if tuning.is_locked("traits.build"):
            kw["build"] = tuning.get("traits.build")
        for name in (
            "skin_palette_idx", "hair_palette_idx", "eye_palette_idx",
            "hair_style_idx", "beard_style_idx",
        ):
            path = f"traits.{name}"
            if tuning.is_locked(path):
                kw[name] = int(tuning.get(path))
        if kw:
            rng = _rng(spec)
            beard_idx = -1
            if race.allow_beard and race.beard_styles:
                if spec.seed % 3 != 0:
                    beard_idx = rng.randrange(len(race.beard_styles))
            base = TraitRoll(
                height_bias=kw.get("height_bias", rng.random()),
                build=kw.get("build", builds[rng.randrange(3)]),
                face_width=kw.get("face_width", rng.random()),
                jaw=kw.get("jaw", rng.random()),
                nose=kw.get("nose", rng.random()),
                brow=kw.get("brow", rng.random()),
                skin_palette_idx=kw.get("skin_palette_idx", rng.randrange(len(race.palette_slots.skin))),
                hair_palette_idx=kw.get("hair_palette_idx", rng.randrange(len(race.palette_slots.hair))),
                eye_palette_idx=kw.get("eye_palette_idx", rng.randrange(len(race.palette_slots.eye))),
                hair_style_idx=kw.get(
                    "hair_style_idx",
                    rng.randrange(len(race.hair_styles)) if race.hair_styles else 0,
                ),
                beard_style_idx=kw.get("beard_style_idx", beard_idx),
                asymmetry=kw.get("asymmetry", rng.random() * 0.05),
                feature_roll=kw.get("feature_roll", rng.random()),
            )
            return base

    rng = _rng(spec)
    builds: tuple[BuildKind, ...] = ("lean", "average", "heavy")
    beard_idx = -1
    if race.allow_beard and race.beard_styles:
        if spec.seed % 3 != 0:
            beard_idx = rng.randrange(len(race.beard_styles))
    return TraitRoll(
        height_bias=rng.random(),
        build=builds[rng.randrange(3)],
        face_width=rng.random(),
        jaw=rng.random(),
        nose=rng.random(),
        brow=rng.random(),
        skin_palette_idx=rng.randrange(len(race.palette_slots.skin)),
        hair_palette_idx=rng.randrange(len(race.palette_slots.hair)),
        eye_palette_idx=rng.randrange(len(race.palette_slots.eye)),
        hair_style_idx=rng.randrange(len(race.hair_styles)) if race.hair_styles else 0,
        beard_style_idx=beard_idx,
        asymmetry=rng.random() * 0.05,
        feature_roll=rng.random(),
    )


def resolve_features(traits: TraitRoll, race: RaceDef, hair_style_id: str) -> list[str]:
    out: list[str] = []
    for rule in race.feature_rules:
        if isinstance(rule, str):
            if rule == "vine_hair" and hair_style_id != "bald":
                out.append(rule)
            elif rule not in ("vine_hair",):
                out.append(rule)
        elif isinstance(rule, FeatureRule):
            if traits.feature_roll >= rule.seed_threshold:
                out.append(rule.id)
    if race.ear_type == "pointed" and "ears_pointed" not in out:
        out.append("ears_pointed")
    seen: set[str] = set()
    unique: list[str] = []
    for f in out:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique
