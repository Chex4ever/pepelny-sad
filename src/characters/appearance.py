"""Appearance cache helpers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.characters.bake import CharacterPoseSet, bake_pose_set
from src.characters.spec import CharacterSpec

if TYPE_CHECKING:
    from src.progression.player_profile import PlayerProfile


def default_appearance() -> CharacterSpec:
    return CharacterSpec(race_id="human", seed=42, age_years=28)


def invalidate_appearance(profile: PlayerProfile) -> None:
    profile._pose_cache = None


def get_pose_set(profile: PlayerProfile) -> CharacterPoseSet:
    if profile._pose_cache is None:
        profile._pose_cache = bake_pose_set(profile.appearance)
    return profile._pose_cache
