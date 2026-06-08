"""Level editor UI state."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LevelEditorState:
    """Selection and active tool for level editor."""

    active_tool: str = "select"
    active_stencil: str = "grass"
    active_structure: str = "bush_low"
    active_biome: str = "meadow"
    expanded_folders: set[str] = field(default_factory=lambda: {"tools", "floor"})
    selected_wx: int | None = None
    selected_wy: int | None = None
    road_points: list[tuple[int, int]] = field(default_factory=list)
    map_path: str | None = None

    def clear_selection(self) -> None:
        self.selected_wx = None
        self.selected_wy = None

    def select_tile(self, wx: int, wy: int) -> None:
        self.selected_wx = wx
        self.selected_wy = wy

    def focus_tile_in_palette(self, *, stencil: str) -> None:
        """Jump to floor template in palette for the selected tile."""
        self.active_stencil = stencil
        self.expanded_folders.add("floor")

    def toggle_folder(self, folder_id: str) -> None:
        if folder_id in self.expanded_folders:
            self.expanded_folders.discard(folder_id)
        else:
            self.expanded_folders.add(folder_id)

    def apply_palette_item(self, item_id: str, kind: str) -> None:
        if kind == "tool":
            self.active_tool = item_id
        elif kind == "stencil":
            self.active_tool = "paint"
            self.active_stencil = item_id
        elif kind == "structure":
            self.active_tool = "structure"
            self.active_structure = item_id
        elif kind == "vegetation":
            self.active_tool = item_id
        elif kind == "generator":
            self.active_tool = item_id
