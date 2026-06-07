"""Top/section slice display modes for tree showcase."""
from __future__ import annotations

from typing import Literal

SliceViewMode = Literal["slice", "rear", "off"]

SLICE_VIEW_MODES: tuple[SliceViewMode, ...] = ("slice", "rear", "off")
SLICE_VIEW_LABELS = {
    "slice": "slice",
    "rear": "rear-cull",
    "off": "off",
}


def cycle_slice_view_mode(mode: SliceViewMode) -> SliceViewMode:
    i = SLICE_VIEW_MODES.index(mode)
    return SLICE_VIEW_MODES[(i + 1) % len(SLICE_VIEW_MODES)]
