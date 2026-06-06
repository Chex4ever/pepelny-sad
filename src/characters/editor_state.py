"""Shared editor state for character + animation editor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.characters.voxel_edits import VoxelEditLayer

PartVisibilityMode = Literal["all", "solo", "hide"]
PaintTool = Literal["add", "remove"]
EditorMode = Literal["generator", "character"]
VoxelPos = tuple[int, int, int]


@dataclass
class EditorState:
    mode: EditorMode = "generator"
    selected_kind: str = "body_torso"
    selected_voxel: VoxelPos | None = None
    visibility_mode: PartVisibilityMode = "all"
    paint_tool: PaintTool = "add"
    voxel_edits: VoxelEditLayer = field(default_factory=VoxelEditLayer)
    settings_collapsed: bool = False

    def kind_filter(self) -> set[str] | None:
        if self.visibility_mode != "solo":
            return None
        return {self.selected_kind}

    def hidden_kinds(self) -> set[str] | None:
        if self.visibility_mode != "hide":
            return None
        return {self.selected_kind}

    def clear_edits(self) -> None:
        self.voxel_edits.clear()
        self.selected_voxel = None

    def toggle_mode(self) -> None:
        self.mode = "character" if self.mode == "generator" else "generator"
        self.settings_collapsed = self.mode == "character"

    def set_mode(self, mode: EditorMode) -> None:
        self.mode = mode
        self.settings_collapsed = mode == "character"

    def select_voxel(self, pos: VoxelPos | None, kind: str | None = None) -> None:
        self.selected_voxel = pos
        if kind:
            self.selected_kind = kind

    def deselect(self) -> None:
        self.selected_voxel = None
