"""Build CharacterMorphology from spec."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.characters.lifecycle import (
    resolve_life_stage,
    stage_head_scale,
    stage_height_multiplier,
    stage_limb_multiplier,
    stage_posture_slouch,
)
from src.characters.loader import load_race
from src.characters.morphology import (
    AnchorPoint,
    BodyProportions,
    BodySegment,
    CharacterMorphology,
    LifeStage,
)
from src.characters.spec import CharacterSpec
from src.characters.traits import resolve_features, roll_traits
from src.characters.tuning import apply_morphology_overrides, apply_race_overrides

if TYPE_CHECKING:
    from src.characters.tuning import TuningState

_DEFAULT_FRAC = {
    "foot": 0.035,
    "calf": 0.215,
    "thigh": 0.215,
    "pelvis": 0.085,
    "torso": 0.285,
    "neck": 0.045,
    "head": 0.125,
    "shoulder_hw": 0.18,
    "hip_hw": 0.105,
    "chest_depth": 0.095,
    "thigh_r": 0.068,
    "calf_r": 0.050,
    "upper_arm_r": 0.036,
    "forearm_r": 0.030,
    "head_r": 0.068,
    "neck_r": 0.030,
    "foot_r": 0.028,
}


def _frac(name: str, tuning: TuningState | None) -> float:
    path = f"gen.frac.{name}"
    if tuning and tuning.is_locked(path):
        return float(tuning.get(path))
    return _DEFAULT_FRAC[name]


def _build_multiplier(traits) -> tuple[float, float]:
    if traits.build == "lean":
        return 0.92, 0.94
    if traits.build == "heavy":
        return 1.08, 1.06
    return 1.0, 1.0


def _sex_modifiers(sex: str, tuning: TuningState | None) -> tuple[float, float]:
    if tuning and tuning.is_locked("gen.sex.shoulder_mod"):
        shoulder = float(tuning.get("gen.sex.shoulder_mod"))
    elif sex == "male":
        shoulder = 1.06
    elif sex == "female":
        shoulder = 0.94
    else:
        shoulder = 1.0
    if tuning and tuning.is_locked("gen.sex.hip_mod"):
        hip = float(tuning.get("gen.sex.hip_mod"))
    elif sex == "male":
        hip = 0.94
    elif sex == "female":
        hip = 1.06
    else:
        hip = 1.0
    return shoulder, hip


def generate_morphology(spec: CharacterSpec, tuning: TuningState | None = None) -> CharacterMorphology:
    race = apply_race_overrides(load_race(spec.race_id), tuning)
    traits = roll_traits(spec, race, tuning)
    stage = resolve_life_stage(spec.age_years, race)

    h_lo, h_hi = race.height_m
    base_h = h_lo + (h_hi - h_lo) * traits.height_bias
    height_m = base_h * stage_height_multiplier(stage, traits.height_bias)

    shoulder_mod, hip_mod = _sex_modifiers(spec.sex, tuning)
    shoulder_scale, limb_r = _build_multiplier(traits)
    shoulder_scale *= race.shoulder_scale * shoulder_mod
    limb_r *= race.limb_scale

    head_scale = stage_head_scale(stage, race.head_scale)
    head_scale *= 0.88 + traits.face_width * 0.24
    limb_stage = stage_limb_multiplier(stage)
    slouch = stage_posture_slouch(stage, race.posture_rigid)

    h = height_m
    foot_h = h * _frac("foot", tuning)
    calf_h = h * _frac("calf", tuning) * limb_stage
    thigh_h = h * _frac("thigh", tuning) * limb_stage * race.limb_ratios.leg
    pelvis_h = h * _frac("pelvis", tuning)
    torso_h = h * _frac("torso", tuning) * race.torso_scale
    neck_h = h * _frac("neck", tuning)
    head_h = h * _frac("head", tuning) * head_scale

    shoulder_hw = h * _frac("shoulder_hw", tuning) * shoulder_scale
    hip_hw = h * _frac("hip_hw", tuning) * hip_mod * race.torso_scale * 0.95
    chest_depth = h * _frac("chest_depth", tuning) * race.torso_scale
    thigh_r = h * _frac("thigh_r", tuning) * limb_r
    calf_r = h * _frac("calf_r", tuning) * limb_r
    upper_arm_r = h * _frac("upper_arm_r", tuning) * limb_r * race.limb_ratios.arm
    forearm_r = h * _frac("forearm_r", tuning) * limb_r * race.limb_ratios.arm
    head_r = h * _frac("head_r", tuning) * head_scale * (0.92 + traits.jaw * 0.08 * race.jaw_scale)
    neck_r = h * _frac("neck_r", tuning)
    foot_r = h * _frac("foot_r", tuning)
    leg_spread = hip_hw * 0.72 + traits.asymmetry

    z_ankle = foot_h * 0.55
    z_knee = foot_h + calf_h
    z_hip = foot_h + calf_h + thigh_h
    z_waist = z_hip + pelvis_h * 0.35
    z_chest = z_hip + pelvis_h + torso_h * 0.55
    z_shoulder = z_hip + pelvis_h + torso_h * 0.90
    z_neck_base = z_hip + pelvis_h + torso_h
    z_head_center = z_neck_base + neck_h + head_h * 0.42
    z_head_top = z_neck_base + neck_h + head_h

    slouch_z = slouch * h
    upper_slouch = slouch_z

    joints = {
        "ankle_l": AnchorPoint(-leg_spread, 0.0, z_ankle),
        "ankle_r": AnchorPoint(leg_spread, 0.0, z_ankle),
        "knee_l": AnchorPoint(-leg_spread, 0.0, z_knee),
        "knee_r": AnchorPoint(leg_spread, 0.0, z_knee),
        "hip_l": AnchorPoint(-leg_spread * 0.95, 0.0, z_hip),
        "hip_r": AnchorPoint(leg_spread * 0.95, 0.0, z_hip),
        "waist": AnchorPoint(0.0, chest_depth * 0.15, z_waist),
        "chest": AnchorPoint(0.0, chest_depth * 0.35, z_chest + upper_slouch),
        "shoulder_l": AnchorPoint(-shoulder_hw, 0.0, z_shoulder + upper_slouch),
        "shoulder_r": AnchorPoint(shoulder_hw, 0.0, z_shoulder + upper_slouch),
        "elbow_l": AnchorPoint(-shoulder_hw - upper_arm_r * 0.3, 0.0, z_chest - upper_arm_r * 2 + upper_slouch),
        "elbow_r": AnchorPoint(shoulder_hw + upper_arm_r * 0.3, 0.0, z_chest - upper_arm_r * 2 + upper_slouch),
        "wrist_l": AnchorPoint(-shoulder_hw - upper_arm_r * 0.6, 0.0, z_hip + pelvis_h * 0.5 + upper_slouch),
        "wrist_r": AnchorPoint(shoulder_hw + upper_arm_r * 0.6, 0.0, z_hip + pelvis_h * 0.5 + upper_slouch),
        "neck_base": AnchorPoint(0.0, neck_r * 0.4, z_neck_base + upper_slouch),
        "head_center": AnchorPoint(0.0, head_r * 0.25, z_head_center + upper_slouch),
        "head_top": AnchorPoint(0.0, 0.0, z_head_top + upper_slouch),
    }

    proportions = BodyProportions(
        shoulder_hw=shoulder_hw,
        hip_hw=hip_hw,
        chest_depth=chest_depth,
        thigh_r=thigh_r,
        calf_r=calf_r,
        upper_arm_r=upper_arm_r,
        forearm_r=forearm_r,
        head_r=head_r,
        neck_r=neck_r,
        foot_r=foot_r,
        leg_spread=leg_spread,
        head_h=head_h,
        neck_h=neck_h,
        torso_h=torso_h,
        pelvis_h=pelvis_h,
        thigh_h=thigh_h,
        calf_h=calf_h,
        foot_h=foot_h,
    )

    segments: list[BodySegment] = [
        BodySegment("leg_l", thigh_h + calf_h, thigh_r, -leg_spread, 0, 0, 0.88),
        BodySegment("leg_r", thigh_h + calf_h, thigh_r, leg_spread, 0, 0, 0.88),
        BodySegment("pelvis", pelvis_h, hip_hw, 0, 0, z_hip, 0.85),
        BodySegment("torso", torso_h, shoulder_hw * 0.85, 0, 0, z_hip + pelvis_h, 0.82),
        BodySegment("arm_l", upper_arm_r * 6, upper_arm_r, -shoulder_hw, 0, z_shoulder, 0.9),
        BodySegment("arm_r", upper_arm_r * 6, upper_arm_r, shoulder_hw, 0, z_shoulder, 0.9),
        BodySegment("neck", neck_h, neck_r, 0, 0, z_neck_base, 0.9),
        BodySegment("head", head_h, head_r, 0, 0, z_neck_base + neck_h, 0.92),
    ]

    hair_style_id = race.hair_styles[traits.hair_style_idx] if race.hair_styles else "bald"
    beard_style_id = None
    if traits.beard_style_idx >= 0 and race.beard_styles:
        beard_style_id = race.beard_styles[traits.beard_style_idx]

    if stage == LifeStage.ELDER and spec.age_years >= race.grey_hair_age:
        hair_palette = "hair_grey"
    else:
        hair_palette = race.palette_slots.hair[traits.hair_palette_idx]

    skin_kind = "skin_ghost" if race.body_opacity < 1.0 else "skin"
    palette = {
        "skin": race.palette_slots.skin[traits.skin_palette_idx],
        "hair": hair_palette,
        "eye": race.palette_slots.eye[traits.eye_palette_idx],
        "skin_kind": skin_kind,
    }

    features = resolve_features(traits, race, hair_style_id)
    if traits.nose > 0.35:
        features.append("nose_prominent")

    anchors = {
        "head_top": joints["head_top"],
        "head_crown": AnchorPoint(0, 0, z_head_center + head_h * 0.35 + upper_slouch),
        "neck_front": AnchorPoint(0, head_r * 0.55, z_neck_base + neck_h * 0.4 + upper_slouch),
        "chest_front": AnchorPoint(0, chest_depth * 0.55, z_chest + upper_slouch),
        "waist": joints["waist"],
        "hand_l_grip": joints["wrist_l"],
        "hand_r_grip": joints["wrist_r"],
        "leg_l": joints["knee_l"],
        "leg_r": joints["knee_r"],
    }

    morph = CharacterMorphology(
        race_id=spec.race_id,
        life_stage=stage,
        age_years=spec.age_years,
        height_m=height_m,
        segments=segments,
        anchors=anchors,
        joints=joints,
        proportions=proportions,
        traits=traits,
        palette=palette,
        features=features,
        seed=spec.seed,
        sex=spec.sex,
        hair_style_id=hair_style_id,
        beard_style_id=beard_style_id,
    )
    return apply_morphology_overrides(morph, tuning, base_proportions=proportions)


def rebuild_skeleton_from_proportions(morph: CharacterMorphology) -> None:
    """Recompute joints/anchors from BodyProportions so limbs stay attached to torso."""
    p = morph.proportions
    if p is None:
        return

    race = load_race(morph.race_id)
    slouch = stage_posture_slouch(morph.life_stage, race.posture_rigid)
    upper_slouch = slouch * morph.height_m

    z_ankle = p.foot_h * 0.55
    z_knee = p.foot_h + p.calf_h
    z_hip = p.foot_h + p.calf_h + p.thigh_h
    z_waist = z_hip + p.pelvis_h * 0.35
    z_chest = z_hip + p.pelvis_h + p.torso_h * 0.55
    z_shoulder = z_hip + p.pelvis_h + p.torso_h * 0.90
    z_neck_base = z_hip + p.pelvis_h + p.torso_h
    z_head_center = z_neck_base + p.neck_h + p.head_h * 0.42
    z_head_top = z_neck_base + p.neck_h + p.head_h

    spread = p.leg_spread
    sh = p.shoulder_hw
    ua = p.upper_arm_r

    morph.joints = {
        "ankle_l": AnchorPoint(-spread, 0.0, z_ankle),
        "ankle_r": AnchorPoint(spread, 0.0, z_ankle),
        "knee_l": AnchorPoint(-spread, 0.0, z_knee),
        "knee_r": AnchorPoint(spread, 0.0, z_knee),
        "hip_l": AnchorPoint(-spread * 0.95, 0.0, z_hip),
        "hip_r": AnchorPoint(spread * 0.95, 0.0, z_hip),
        "waist": AnchorPoint(0.0, p.chest_depth * 0.15, z_waist),
        "chest": AnchorPoint(0.0, p.chest_depth * 0.35, z_chest + upper_slouch),
        "shoulder_l": AnchorPoint(-sh, 0.0, z_shoulder + upper_slouch),
        "shoulder_r": AnchorPoint(sh, 0.0, z_shoulder + upper_slouch),
        "elbow_l": AnchorPoint(-sh - ua * 0.3, 0.0, z_chest - ua * 2 + upper_slouch),
        "elbow_r": AnchorPoint(sh + ua * 0.3, 0.0, z_chest - ua * 2 + upper_slouch),
        "wrist_l": AnchorPoint(-sh - ua * 0.6, 0.0, z_hip + p.pelvis_h * 0.5 + upper_slouch),
        "wrist_r": AnchorPoint(sh + ua * 0.6, 0.0, z_hip + p.pelvis_h * 0.5 + upper_slouch),
        "neck_base": AnchorPoint(0.0, p.neck_r * 0.4, z_neck_base + upper_slouch),
        "head_center": AnchorPoint(0.0, p.head_r * 0.25, z_head_center + upper_slouch),
        "head_top": AnchorPoint(0.0, 0.0, z_head_top + upper_slouch),
    }

    morph.anchors = {
        "head_top": morph.joints["head_top"],
        "head_crown": AnchorPoint(0, 0, z_head_center + p.head_h * 0.35 + upper_slouch),
        "neck_front": AnchorPoint(0, p.head_r * 0.55, z_neck_base + p.neck_h * 0.4 + upper_slouch),
        "chest_front": AnchorPoint(0, p.chest_depth * 0.55, z_chest + upper_slouch),
        "waist": morph.joints["waist"],
        "hand_l_grip": morph.joints["wrist_l"],
        "hand_r_grip": morph.joints["wrist_r"],
        "leg_l": morph.joints["knee_l"],
        "leg_r": morph.joints["knee_r"],
    }
