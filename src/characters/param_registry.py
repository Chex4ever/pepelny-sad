"""Registry of tunable character generator parameters for the dev tuner UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ParamKind = Literal["float", "int", "enum", "bool", "str", "readonly"]


@dataclass(frozen=True)
class ParamDef:
    path: str
    group: str
    label_ru: str
    description_ru: str
    kind: ParamKind
    step: float = 1.0
    min: float | None = None
    max: float | None = None
    enum_values: tuple[str, ...] | None = None
    export_hint: str = ""


def _spec_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("spec.race_id", "Spec", "раса (id)", "Ключ расы в races.json", "str", export_hint="spec / CLI"),
        ParamDef("spec.seed", "Spec", "seed", "RNG-сид черт и палитры", "int", step=1, min=0, max=2_000_000_000),
        ParamDef("spec.age_years", "Spec", "возраст", "Возраст в годах", "float", step=1, min=1, max=1000),
        ParamDef(
            "spec.sex", "Spec", "пол", "male/female/neutral", "enum",
            enum_values=("male", "female", "neutral"),
        ),
    )


def _trait_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("traits.height_bias", "Traits", "height_bias", "Смещение роста в диапазоне расы", "float", step=0.01, min=0, max=1),
        ParamDef("traits.build", "Traits", "build", "Телосложение", "enum", enum_values=("lean", "average", "heavy")),
        ParamDef("traits.face_width", "Traits", "face_width", "Ширина лица → масштаб головы", "float", step=0.01, min=0, max=1),
        ParamDef("traits.jaw", "Traits", "jaw", "Челюсть → head_r", "float", step=0.01, min=0, max=1),
        ParamDef("traits.nose", "Traits", "nose", ">0.35 → nose_prominent", "float", step=0.01, min=0, max=1),
        ParamDef("traits.brow", "Traits", "brow", "Брови (пока не используется)", "float", step=0.01, min=0, max=1),
        ParamDef("traits.skin_palette_idx", "Traits", "skin_palette_idx", "Индекс палитры кожи", "int", step=1, min=0, max=8),
        ParamDef("traits.hair_palette_idx", "Traits", "hair_palette_idx", "Индекс палитры волос", "int", step=1, min=0, max=8),
        ParamDef("traits.eye_palette_idx", "Traits", "eye_palette_idx", "Индекс палитры глаз", "int", step=1, min=0, max=8),
        ParamDef("traits.hair_style_idx", "Traits", "hair_style_idx", "Индекс причёски расы", "int", step=1, min=0, max=8),
        ParamDef("traits.beard_style_idx", "Traits", "beard_style_idx", "-1 = нет бороды", "int", step=1, min=-1, max=8),
        ParamDef("traits.asymmetry", "Traits", "asymmetry", "Разведение ног", "float", step=0.001, min=0, max=0.05),
        ParamDef("traits.feature_roll", "Traits", "feature_roll", "Порог расовых feature_rules", "float", step=0.01, min=0, max=1),
    )


def _race_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("race.height_m.0", "Race", "height_m min", "Мин. рост расы (м)", "float", step=0.01, min=0.5, max=3, export_hint="races.json"),
        ParamDef("race.height_m.1", "Race", "height_m max", "Макс. рост расы (м)", "float", step=0.01, min=0.5, max=3, export_hint="races.json"),
        ParamDef("race.shoulder_scale", "Race", "shoulder_scale", "Ширина плеч", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.limb_scale", "Race", "limb_scale", "Масштаб конечностей", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.head_scale", "Race", "head_scale", "Масштаб головы", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.torso_scale", "Race", "torso_scale", "Масштаб торса", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.limb_ratios.arm", "Race", "limb_ratios.arm", "Длина/радиус рук", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.limb_ratios.leg", "Race", "limb_ratios.leg", "Длина/радиус ног", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.limb_ratios.neck", "Race", "limb_ratios.neck", "Шея (загружается, не используется)", "float", step=0.01, min=0, max=0.2),
        ParamDef("race.jaw_scale", "Race", "jaw_scale", "Масштаб челюсти", "float", step=0.01, min=0.5, max=2, export_hint="races.json"),
        ParamDef("race.ear_length_m", "Race", "ear_length_m", "Длина ушей (м)", "float", step=0.005, min=0, max=0.15, export_hint="races.json"),
    )


def _lifecycle_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("life_stage", "Lifecycle", "life_stage", "Стадия жизни (read-only)", "readonly"),
        ParamDef("lifecycle.stage_height_multiplier", "Lifecycle", "stage_height_mult", "Множитель роста стадии", "float", step=0.01, min=0.5, max=1.5),
        ParamDef("lifecycle.stage_head_scale", "Lifecycle", "stage_head_scale", "Множитель головы стадии", "float", step=0.01, min=0.5, max=2),
        ParamDef("lifecycle.stage_limb_multiplier", "Lifecycle", "stage_limb_mult", "Множитель конечностей", "float", step=0.01, min=0.5, max=1.5),
        ParamDef("lifecycle.stage_posture_slouch", "Lifecycle", "stage_slouch", "Осанка (отриц. = сутулость)", "float", step=0.005, min=-0.1, max=0.1),
    )


def _proportion_params() -> tuple[ParamDef, ...]:
    fields = (
        "shoulder_hw", "hip_hw", "chest_depth", "thigh_r", "calf_r", "upper_arm_r", "forearm_r",
        "head_r", "neck_r", "foot_r", "leg_spread", "head_h", "neck_h", "torso_h", "pelvis_h",
        "thigh_h", "calf_h", "foot_h",
    )
    return tuple(
        ParamDef(f"proportions.{name}", "Proportions", name, f"BodyProportions.{name} (м)", "float", step=0.005, min=0, max=2)
        for name in fields
    ) + (
        ParamDef("morphology.height_m", "Proportions", "height_m", "Итоговый рост (м)", "float", step=0.01, min=0.5, max=3),
    )


def _gen_frac_params() -> tuple[ParamDef, ...]:
    fracs = (
        "foot", "calf", "thigh", "pelvis", "torso", "neck", "head", "shoulder_hw", "hip_hw",
        "chest_depth", "thigh_r", "calf_r", "upper_arm_r", "forearm_r", "head_r", "neck_r", "foot_r",
    )
    return tuple(
        ParamDef(
            f"gen.frac.{name}", "Generate", f"frac.{name}",
            f"Доля роста → {name} в generate.py", "float", step=0.005, min=0, max=0.5,
            export_hint="generate.py _DEFAULT_FRAC",
        )
        for name in fracs
    ) + (
        ParamDef("gen.sex.shoulder_mod", "Generate", "sex.shoulder_mod", "Модификатор плеч по полу", "float", step=0.01, min=0.8, max=1.2),
        ParamDef("gen.sex.hip_mod", "Generate", "sex.hip_mod", "Модификатор бёдер по полу", "float", step=0.01, min=0.8, max=1.2),
    )


def _joint_params() -> tuple[ParamDef, ...]:
    joints = (
        "ankle_l", "ankle_r", "knee_l", "knee_r", "hip_l", "hip_r", "waist", "chest",
        "shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r",
        "neck_base", "head_center", "head_top",
    )
    out: list[ParamDef] = []
    for j in joints:
        for axis in ("x", "y", "z"):
            out.append(
                ParamDef(
                    f"joint.{j}.{axis}", "Joints", f"{j}.{axis}",
                    f"Сустав {j} ({axis}), м", "float", step=0.005, min=-2, max=2,
                )
            )
    return tuple(out)


def _voxel_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("voxel.tiles_per_m_xy", "Voxel", "tiles_per_m_xy", "Гориз. тайлов на метр", "float", step=0.5, min=1, max=20, export_hint="adapters/voxel.py"),
        ParamDef("voxel.tiles_per_m_z", "Voxel", "tiles_per_m_z", "Верт. тайлов на метр", "float", step=0.5, min=1, max=20),
        ParamDef("voxel.min_rxy_arm", "Voxel", "min_rxy_arm", "Мин. радиус руки (тайлы)", "float", step=0.02, min=0.2, max=2),
        ParamDef("voxel.min_rxy_leg", "Voxel", "min_rxy_leg", "Мин. радиус ноги", "float", step=0.02, min=0.2, max=2),
        ParamDef("voxel.min_rxy_torso", "Voxel", "min_rxy_torso", "Мин. радиус торса", "float", step=0.02, min=0.2, max=2),
        ParamDef("voxel.min_rxy_head", "Voxel", "min_rxy_head", "Мин. радиус головы", "float", step=0.02, min=0.5, max=3),
        ParamDef("voxel.min_rz", "Voxel", "min_rz", "Мин. радиус по Z", "float", step=0.02, min=0.1, max=2),
        ParamDef("voxel.torso_steps", "Voxel", "torso_steps", "Слоёв торса", "int", step=1, min=3, max=20),
    )


def _anim_params() -> tuple[ParamDef, ...]:
    return (
        ParamDef("anim.walk_period_s", "Anim", "walk_period_s", "Период шага (с)", "float", step=0.02, min=0.1, max=2),
    )


PARAM_REGISTRY: tuple[ParamDef, ...] = (
    *_spec_params(),
    *_trait_params(),
    *_race_params(),
    *_lifecycle_params(),
    *_proportion_params(),
    *_gen_frac_params(),
    *_joint_params(),
    *_voxel_params(),
    *_anim_params(),
)

PARAM_BY_PATH: dict[str, ParamDef] = {p.path: p for p in PARAM_REGISTRY}

GROUP_ORDER: tuple[str, ...] = (
    "Spec", "Traits", "Race", "Lifecycle", "Proportions", "Generate", "Joints", "Voxel", "Anim",
)


def params_by_group() -> dict[str, list[ParamDef]]:
    out: dict[str, list[ParamDef]] = {g: [] for g in GROUP_ORDER}
    for p in PARAM_REGISTRY:
        out.setdefault(p.group, []).append(p)
    return out
