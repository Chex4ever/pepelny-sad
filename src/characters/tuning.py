"""Character generator tuning state, reference snapshots, and export."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime, timezone
from typing import Any

from src.characters.loader import load_race
from src.characters.morphology import AnchorPoint, BodyProportions, CharacterMorphology, LifeStage, TraitRoll
from src.characters.race import RaceDef
from src.characters.spec import CharacterSpec
from src.characters.traits import roll_traits

FlatSnapshot = dict[str, Any]

_LIFE_STAGE_RU = {
    LifeStage.CHILD: "ребёнок",
    LifeStage.YOUNG: "юный",
    LifeStage.ADULT: "взрослый",
    LifeStage.ELDER: "старик",
}


@dataclass
class TuningState:
    overrides: dict[str, Any] = field(default_factory=dict)
    locked: set[str] = field(default_factory=set)
    proportion_scale: float = 1.0

    def is_locked(self, path: str) -> bool:
        return path in self.locked

    def get(self, path: str, default: Any = None) -> Any:
        if path in self.overrides:
            return self.overrides[path]
        return default

    def set(self, path: str, value: Any) -> None:
        self.overrides[path] = value
        self.locked.add(path)

    def reset(self, path: str) -> None:
        self.overrides.pop(path, None)
        self.locked.discard(path)

    def reset_prefix(self, prefix: str) -> None:
        to_drop = [p for p in self.overrides if p.startswith(prefix)]
        for p in to_drop:
            self.reset(p)

    def reset_all(self) -> None:
        self.overrides.clear()
        self.locked.clear()
        self.proportion_scale = 1.0

    def to_dict(self) -> dict:
        return {
            "overrides": dict(self.overrides),
            "locked": sorted(self.locked),
            "proportion_scale": self.proportion_scale,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TuningState:
        state = cls()
        state.overrides = dict(data.get("overrides", {}))
        state.locked = set(data.get("locked", []))
        state.proportion_scale = float(data.get("proportion_scale", 1.0))
        return state

    def diff_vs(self, reference: FlatSnapshot) -> dict[str, tuple[Any, Any]]:
        out: dict[str, tuple[Any, Any]] = {}
        for path in sorted(self.locked):
            if path not in self.overrides:
                continue
            cur = self.overrides[path]
            ref = reference.get(path)
            if cur != ref:
                out[path] = (cur, ref)
        return out

    def export_bundle(self, spec: CharacterSpec, reference: FlatSnapshot) -> dict:
        bundle = {
            "meta": {
                "race_id": spec.race_id,
                "age_years": spec.age_years,
                "seed": spec.seed,
                "sex": spec.sex,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
            "overrides": {p: self.overrides[p] for p in sorted(self.locked) if p in self.overrides},
            "diff": {p: {"value": v, "ref": reference.get(p)} for p, (v, _r) in self.diff_vs(reference).items()},
        }
        if abs(self.proportion_scale - 1.0) > 1e-6:
            bundle["proportion_scale"] = self.proportion_scale
        return bundle

    def export_diff_text(self, spec: CharacterSpec, reference: FlatSnapshot) -> str:
        lines = [
            f"# Overrides vs reference ({spec.race_id}, age={spec.age_years:.0f}, seed={spec.seed})",
        ]
        for path, (val, ref) in sorted(self.diff_vs(reference).items()):
            lines.append(f"{path}: {val}  (ref {ref})")
        return "\n".join(lines) + "\n"


@dataclass
class SpecController:
    """Shared spec state for RaceAgeBar and ParamRow."""

    race_id: str = "human"
    age_years: float = 28.0
    seed: int = 42
    sex: str = "neutral"
    equipment: dict[str, str | None] = field(default_factory=dict)

    def to_spec(self) -> CharacterSpec:
        return CharacterSpec(
            race_id=self.race_id,
            seed=self.seed,
            age_years=self.age_years,
            sex=self.sex,  # type: ignore[arg-type]
            equipment=dict(self.equipment),
        )

    def apply_spec_overrides(self, tuning: TuningState) -> None:
        if tuning.is_locked("spec.race_id"):
            self.race_id = str(tuning.get("spec.race_id", self.race_id))
        if tuning.is_locked("spec.age_years"):
            self.age_years = float(tuning.get("spec.age_years", self.age_years))
        if tuning.is_locked("spec.seed"):
            self.seed = int(tuning.get("spec.seed", self.seed))
        if tuning.is_locked("spec.sex"):
            self.sex = str(tuning.get("spec.sex", self.sex))

    def sync_from_spec(self, spec: CharacterSpec) -> None:
        self.race_id = spec.race_id
        self.age_years = spec.age_years
        self.seed = spec.seed
        self.sex = spec.sex
        self.equipment = dict(spec.equipment)

    def clamp_age_to_race(self) -> None:
        race = load_race(self.race_id)
        self.age_years = max(1.0, min(float(race.max_age_years), self.age_years))


def stage_preset_age(race: RaceDef, stage: LifeStage) -> float:
    t = race.age_thresholds
    if stage == LifeStage.CHILD:
        return max(1.0, t.child_max * 0.5)
    if stage == LifeStage.YOUNG:
        return (t.child_max + t.young_max) * 0.5
    if stage == LifeStage.ADULT:
        return (t.young_max + t.adult_max) * 0.5
    return (t.adult_max + race.max_age_years) * 0.5


def life_stage_label(stage: LifeStage) -> str:
    return _LIFE_STAGE_RU.get(stage, stage.value)


def apply_race_overrides(race: RaceDef, tuning: TuningState | None) -> RaceDef:
    if not tuning:
        return race
    kw: dict[str, Any] = {}
    for f in fields(race):
        path = f"race.{f.name}"
        if tuning.is_locked(path):
            kw[f.name] = tuning.get(path)
        elif f.name == "height_m" and (
            tuning.is_locked("race.height_m.0") or tuning.is_locked("race.height_m.1")
        ):
            lo = tuning.get("race.height_m.0", race.height_m[0]) if tuning.is_locked("race.height_m.0") else race.height_m[0]
            hi = tuning.get("race.height_m.1", race.height_m[1]) if tuning.is_locked("race.height_m.1") else race.height_m[1]
            kw["height_m"] = (float(lo), float(hi))
        elif f.name == "limb_ratios":
            arm = tuning.get("race.limb_ratios.arm", race.limb_ratios.arm) if tuning.is_locked("race.limb_ratios.arm") else race.limb_ratios.arm
            leg = tuning.get("race.limb_ratios.leg", race.limb_ratios.leg) if tuning.is_locked("race.limb_ratios.leg") else race.limb_ratios.leg
            neck = tuning.get("race.limb_ratios.neck", race.limb_ratios.neck) if tuning.is_locked("race.limb_ratios.neck") else race.limb_ratios.neck
            if tuning.is_locked("race.limb_ratios.arm") or tuning.is_locked("race.limb_ratios.leg") or tuning.is_locked("race.limb_ratios.neck"):
                from src.characters.race import LimbRatios

                kw["limb_ratios"] = LimbRatios(arm=float(arm), leg=float(leg), neck=float(neck))
    if not kw:
        return race
    return replace(race, **kw)


def _trait_field_names() -> tuple[str, ...]:
    return tuple(f.name for f in fields(TraitRoll))


def apply_trait_overrides(traits: TraitRoll, tuning: TuningState | None) -> TraitRoll:
    if not tuning:
        return traits
    kw: dict[str, Any] = {}
    for name in _trait_field_names():
        path = f"traits.{name}"
        if tuning.is_locked(path):
            val = tuning.get(path)
            if name == "build":
                kw[name] = val
            elif name.endswith("_idx"):
                kw[name] = int(val)
            else:
                kw[name] = float(val)
    if not kw:
        return traits
    return replace(traits, **kw)


def apply_proportion_overrides(
    prop: BodyProportions,
    tuning: TuningState | None,
    *,
    traits: TraitRoll | None = None,
    base: BodyProportions | None = None,
) -> BodyProportions:
    if not tuning:
        return prop
    src = base or prop
    scale = tuning.proportion_scale
    kw: dict[str, Any] = {}
    for f in fields(prop):
        path = f"proportions.{f.name}"
        if tuning.is_locked(path):
            kw[f.name] = float(tuning.get(path))
        elif abs(scale - 1.0) > 1e-6:
            kw[f.name] = float(getattr(src, f.name)) * scale
    if "hip_hw" in kw and not tuning.is_locked("proportions.leg_spread"):
        asym = traits.asymmetry if traits else 0.0
        kw["leg_spread"] = kw["hip_hw"] * 0.72 + asym
    elif tuning.is_locked("proportions.hip_hw") and not tuning.is_locked("proportions.leg_spread"):
        asym = traits.asymmetry if traits else 0.0
        kw["leg_spread"] = float(tuning.get("proportions.hip_hw")) * 0.72 + asym
    if not kw:
        return prop
    return replace(prop, **kw)


def apply_joint_overrides(joints: dict[str, AnchorPoint], tuning: TuningState | None) -> dict[str, AnchorPoint]:
    if not tuning:
        return joints
    out = dict(joints)
    for name, ap in joints.items():
        kw: dict[str, float] = {}
        for axis in ("x", "y", "z"):
            path = f"joint.{name}.{axis}"
            if tuning.is_locked(path):
                kw[axis] = float(tuning.get(path))
        if kw:
            out[name] = replace(ap, **kw)
    return out


def apply_morphology_overrides(
    morph: CharacterMorphology,
    tuning: TuningState | None,
    *,
    base_proportions: BodyProportions | None = None,
) -> CharacterMorphology:
    if not tuning or not morph.proportions:
        return morph
    base = base_proportions or morph.proportions
    morph.proportions = apply_proportion_overrides(
        morph.proportions, tuning, traits=morph.traits, base=base,
    )
    prop_changed = (
        any(p.startswith("proportions.") for p in tuning.locked)
        or abs(tuning.proportion_scale - 1.0) > 1e-6
    )
    if prop_changed:
        from src.characters.generate import rebuild_skeleton_from_proportions

        rebuild_skeleton_from_proportions(morph)
    morph.joints = apply_joint_overrides(morph.joints, tuning)
    if tuning.is_locked("morphology.height_m"):
        morph.height_m = float(tuning.get("morphology.height_m"))
    return morph


def flatten_pipeline(spec: CharacterSpec, tuning: TuningState | None = None) -> FlatSnapshot:
    """Flatten spec + morphology + race + lifecycle into dotted paths."""
    from src.characters.adapters.voxel import DEFAULT_VOXEL_BUILD_CONFIG, voxel_build_config_from_tuning
    from src.characters.generate import generate_morphology
    from src.characters.lifecycle import (
        resolve_life_stage,
        stage_head_scale,
        stage_height_multiplier,
        stage_limb_multiplier,
        stage_posture_slouch,
    )

    race = apply_race_overrides(load_race(spec.race_id), tuning)
    traits = apply_trait_overrides(roll_traits(spec, race, tuning), tuning)
    morph = apply_morphology_overrides(generate_morphology(spec, tuning=tuning), tuning)
    stage = resolve_life_stage(spec.age_years, race)
    vcfg = voxel_build_config_from_tuning(tuning) if tuning else DEFAULT_VOXEL_BUILD_CONFIG

    snap: FlatSnapshot = {
        "spec.race_id": spec.race_id,
        "spec.seed": spec.seed,
        "spec.age_years": spec.age_years,
        "spec.sex": spec.sex,
        "life_stage": stage.value,
        "life_stage.label_ru": life_stage_label(stage),
        "lifecycle.stage_height_multiplier": stage_height_multiplier(stage, traits.height_bias),
        "lifecycle.stage_head_scale": stage_head_scale(stage, race.head_scale),
        "lifecycle.stage_limb_multiplier": stage_limb_multiplier(stage),
        "lifecycle.stage_posture_slouch": stage_posture_slouch(stage, race.posture_rigid),
        "morphology.height_m": morph.height_m,
    }

    for name in _trait_field_names():
        snap[f"traits.{name}"] = getattr(traits, name)

    for f in fields(race):
        val = getattr(race, f.name)
        if f.name == "height_m":
            snap["race.height_m.0"] = val[0]
            snap["race.height_m.1"] = val[1]
        elif f.name == "limb_ratios":
            snap["race.limb_ratios.arm"] = val.arm
            snap["race.limb_ratios.leg"] = val.leg
            snap["race.limb_ratios.neck"] = val.neck
        elif f.name in ("palette_slots", "hair_styles", "beard_styles", "feature_rules", "age_thresholds"):
            continue
        else:
            snap[f"race.{f.name}"] = val

    if morph.proportions:
        for f in fields(morph.proportions):
            snap[f"proportions.{f.name}"] = getattr(morph.proportions, f.name)

    for jname, ap in morph.joints.items():
        snap[f"joint.{jname}.x"] = ap.x
        snap[f"joint.{jname}.y"] = ap.y
        snap[f"joint.{jname}.z"] = ap.z

    for f in fields(vcfg):
        snap[f"voxel.{f.name}"] = getattr(vcfg, f.name)

    snap["anim.walk_period_s"] = 0.36
    return snap


def build_reference(spec: CharacterSpec) -> FlatSnapshot:
    return flatten_pipeline(spec, tuning=None)


def build_current_values(spec: CharacterSpec, tuning: TuningState) -> FlatSnapshot:
    base = flatten_pipeline(spec, tuning=None)
    for path in tuning.locked:
        if path in tuning.overrides:
            base[path] = tuning.overrides[path]
    merged = flatten_pipeline(spec, tuning=tuning)
    for path, val in merged.items():
        base[path] = val
    return base


def save_export_bundle(path: str, spec: CharacterSpec, tuning: TuningState, reference: FlatSnapshot) -> None:
    bundle = tuning.export_bundle(spec, reference)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
