"""Unified render API for editors."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame

from src.engine.viewport.bounds import center_origin
from src.engine.viewport.floor import draw_packed_floor
from src.engine.world.queue import build_surface_draw_queue
from src.tools.iso_preview import OverworldPreview, preview_mode_label

if TYPE_CHECKING:
    from src.world.chunk import Chunk


@dataclass
class FloorScene:
    feet_cx: int = 0
    feet_cy: int = 0
    floor_seed: int = 0
    show: bool = True


@dataclass
class WorldScene:
    chunks: list[tuple["Chunk", int, int, int, int]] = field(default_factory=list)
    """(chunk, wx0, wy0, w, h) patches to draw."""

    focus_wx: int = 0
    focus_wy: int = 0
    show: bool = True


@dataclass
class RenderScene:
    floor: FloorScene | None = None
    world: WorldScene | None = None
    hud_lines: list[str] = field(default_factory=list)


class EngineViewport:
    """WYSIWYG viewport: world queue via OverworldPreview, optional packed floor overlay."""

    def __init__(self, mode: str | None = None) -> None:
        self._preview = OverworldPreview(mode=mode)

    @property
    def mode(self) -> str:
        return self._preview.mode

    @property
    def mode_label(self) -> str:
        return preview_mode_label(self.mode)

    @property
    def pixel_w(self) -> int:
        return self._preview.pixel_w

    @property
    def pixel_h(self) -> int:
        return self._preview.pixel_h

    def present_world(
        self,
        scene: WorldScene,
        *,
        hud_lines: list[str] | None = None,
    ) -> None:
        queue: list[tuple] = []
        for chunk, wx0, wy0, w, h in scene.chunks:
            queue.extend(build_surface_draw_queue(chunk, wx0, wy0, w, h))
        queue.sort(key=lambda t: (t[0], t[3]))
        self._preview.present(
            queue,
            focus_wx=scene.focus_wx,
            focus_wy=scene.focus_wy,
            hud_lines=hud_lines,
        )

    def draw_packed_floor_on_surface(
        self,
        surf: pygame.Surface,
        floor: FloorScene,
        *,
        ox: int,
        oy: int,
        cell_w: int,
        cell_h: int,
        font: pygame.font.Font,
        brightness_at=None,
        shade_from_brightness=None,
        floor_shadow: set[tuple[int, int]] | None = None,
    ) -> None:
        if not floor.show:
            return
        draw_packed_floor(
            surf,
            feet_cx=floor.feet_cx,
            feet_cy=floor.feet_cy,
            ox=ox,
            oy=oy,
            cell_w=cell_w,
            cell_h=cell_h,
            font=font,
            floor_seed=floor.floor_seed,
            brightness_at=brightness_at,
            shade_from_brightness=shade_from_brightness,
            floor_shadow=floor_shadow,
        )

    def release(self) -> None:
        self._preview.release()


__all__ = [
    "EngineViewport",
    "FloorScene",
    "RenderScene",
    "WorldScene",
    "center_origin",
]
