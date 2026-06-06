"""Runtime pose selection from baked pose set."""
from __future__ import annotations

import time

from src.characters.bake import CharacterPoseSet
from src.characters.poses import is_valid_facing, pose_key
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel


class AnimPlayer:
    def __init__(self, pose_set: CharacterPoseSet, *, walk_period_s: float = 0.36) -> None:
        self.pose_set = pose_set
        self.facing = "s"
        self.walking = False
        self.paused = False
        self.manual_phase: int | None = None
        self.walk_period_s = walk_period_s
        self._t0 = time.monotonic()

    def set_facing(self, facing: str) -> None:
        if is_valid_facing(facing):
            self.facing = facing

    def set_walking(self, walking: bool) -> None:
        if walking and not self.walking:
            self._t0 = time.monotonic()
        self.walking = walking

    def toggle_pause(self) -> None:
        if not self.paused:
            self.manual_phase = self.walk_phase()
        else:
            self.manual_phase = None
            self._t0 = time.monotonic()
        self.paused = not self.paused

    def set_manual_phase(self, phase: int | None) -> None:
        self.manual_phase = phase if phase is None else int(phase) % 3

    def nudge_phase(self, delta: int) -> None:
        cur = self.manual_phase if self.manual_phase is not None else self.walk_phase()
        self.manual_phase = (cur + delta) % 3

    def walk_phase(self, *, now: float | None = None) -> int:
        if self.manual_phase is not None:
            return self.manual_phase % 3
        if not self.walking or self.paused:
            return 0
        t = (now if now is not None else time.monotonic()) - self._t0
        return int(t / self.walk_period_s * 3) % 3

    def current_pose_id(self, *, now: float | None = None) -> str:
        phase = self.walk_phase(now=now)
        walking = self.walking
        return pose_key(self.facing, walking=walking, phase=phase)

    def current_model(self, *, now: float | None = None) -> TreeVoxelModel:
        return self.pose_set.get(self.current_pose_id(now=now))
