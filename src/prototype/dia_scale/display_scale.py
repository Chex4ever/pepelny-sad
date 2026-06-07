"""Fixed-window display presets for dia_scale prototype."""
from __future__ import annotations

from dataclasses import dataclass

WINDOW_PX_W = 1200
WINDOW_PX_H = 800
TUNER_WINDOW_PX_W = 1600
TUNER_WINDOW_PX_H = 900
TUNER_LEFT_W = 960
TUNER_RIGHT_W = TUNER_WINDOW_PX_W - TUNER_LEFT_W

EDITOR_WINDOW_PX_W = 1800
EDITOR_WINDOW_PX_H = 960
EDITOR_PARTS_W = 160
EDITOR_ANIM_H = 72
EDITOR_PARAMS_W = 640
EDITOR_VIEW_W = EDITOR_WINDOW_PX_W - EDITOR_PARTS_W - EDITOR_PARAMS_W
EDITOR_VIEW_H = EDITOR_WINDOW_PX_H - EDITOR_ANIM_H

HUD_ROWS = 3


@dataclass(frozen=True)
class DisplayPreset:
    name: str
    cell_w: int
    cell_h: int

    @property
    def label(self) -> str:
        return f"{self.name} ({self.cell_w}x{self.cell_h}px)"


PRESET_NORMAL = DisplayPreset("normal", 10, 16)
PRESET_COMPACT = DisplayPreset("compact", 5, 8)
PRESETS: tuple[DisplayPreset, ...] = (PRESET_NORMAL, PRESET_COMPACT)


def visible_chars(preset: DisplayPreset, viewport_w: int | None = None) -> tuple[int, int]:
    """Char cells visible in map band for fixed window (or panel width)."""
    map_h = WINDOW_PX_H - HUD_ROWS * 14 - 8
    w_px = viewport_w if viewport_w is not None else WINDOW_PX_W
    w = max(1, w_px // preset.cell_w)
    h = max(1, map_h // preset.cell_h)
    return w, h


def toggle_preset(current: DisplayPreset) -> DisplayPreset:
    return PRESET_COMPACT if current is PRESET_NORMAL else PRESET_NORMAL


def preset_by_name(name: str) -> DisplayPreset:
    for p in PRESETS:
        if p.name == name:
            return p
    return PRESET_NORMAL
