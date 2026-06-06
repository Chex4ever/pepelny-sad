"""Render cross-section panels for voxel trees."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.prototype.dia_scale.constants import (
    COLOR_BG,
    COLOR_BRANCH_BG,
    COLOR_BRANCH_FG,
    COLOR_CANOPY_BG,
    COLOR_CANOPY_FG,
    COLOR_HUD,
    COLOR_SECTION_BG,
    COLOR_SLICE_LINE,
    COLOR_TRUNK_BG,
    COLOR_TRUNK_FG,
    VOXEL_BRANCH,
    VOXEL_LEAF,
    VOXEL_TRUNK,
)
from src.prototype.dia_scale.cross_section import SectionGrid
from src.prototype.dia_scale.display_scale import DisplayPreset, WINDOW_PX_H, WINDOW_PX_W


_KIND_COLORS = {
    VOXEL_TRUNK: (COLOR_TRUNK_FG, COLOR_TRUNK_BG),
    VOXEL_BRANCH: (COLOR_BRANCH_FG, COLOR_BRANCH_BG),
    VOXEL_LEAF: (COLOR_CANOPY_FG, COLOR_CANOPY_BG),
}


@dataclass
class SectionView:
    pan_x: int = 0
    pan_y: int = 0


class SectionRenderer:
    def __init__(self, *, preset: DisplayPreset, panel_w: int | None = None) -> None:
        self.preset = preset
        self.panel_w = panel_w or WINDOW_PX_W // 2
        self.panel_h = WINDOW_PX_H
        self.view = SectionView()
        self._font = pygame.font.SysFont("consolas", max(6, preset.cell_h - 2))
        self._font_hud = pygame.font.SysFont("consolas", 9)

    def reset_pan(self) -> None:
        self.view.pan_x = 0
        self.view.pan_y = 0

    def pan_pixels(self, dpx: int, dpy: int) -> None:
        if dpx or dpy:
            self.view.pan_x += dpx
            self.view.pan_y += dpy

    def point_in_panel(self, mx: int, my: int, *, panel_x0: int = 0) -> bool:
        return panel_x0 <= mx < panel_x0 + self.panel_w and 0 <= my < self.panel_h

    def set_preset(self, preset: DisplayPreset) -> None:
        self.preset = preset
        self._font = pygame.font.SysFont("consolas", max(6, preset.cell_h - 2))

    def render(
        self,
        section: SectionGrid,
        *,
        title: str,
        hud_extra: str = "",
        z_cut: int | None = None,
        z_cut_mode: str = "slice",
    ) -> pygame.Surface:
        surf = pygame.Surface((self.panel_w, self.panel_h))
        surf.fill(COLOR_SECTION_BG)
        cw, ch = self.preset.cell_w, self.preset.cell_h

        if not section.cells:
            surf.blit(self._font_hud.render("empty section", True, COLOR_HUD), (8, 8))
            return surf

        z_span = section.max_z - section.min_z + 1
        h_span = section.max_h - section.min_h + 1
        margin = 8
        title_h = self._font_hud.get_height() + 4
        avail_w = self.panel_w - margin * 2
        avail_h = self.panel_h - margin * 2 - title_h - 16
        scale = min(avail_w // max(1, h_span * cw), avail_h // max(1, z_span * ch), 2)
        if scale < 1:
            scale = 1
        pcw, pch = cw * scale, ch * scale

        ox = margin + (avail_w - h_span * pcw) // 2 + self.view.pan_x
        oz_base = self.panel_h - margin - pch + self.view.pan_y

        surf.blit(self._font_hud.render(title, True, COLOR_HUD), (margin, margin))

        draw_cells = section.cells
        if z_cut is not None and z_cut_mode == "rear":
            draw_cells = {(h, z): c for (h, z), c in section.cells.items() if z <= z_cut}

        for (h, z), cell in draw_cells.items():
            col = h - section.min_h
            row = z - section.min_z
            px = ox + col * pcw
            py = oz_base - row * pch
            fg, bg = _KIND_COLORS.get(cell.kind, ((200, 200, 200), COLOR_BG))
            rect = pygame.Rect(px, py, pcw, pch)
            pygame.draw.rect(surf, bg, rect)
            if pcw >= 4 and pch >= 6:
                t = self._font.render(cell.ch, True, fg)
                surf.blit(t, (px, py))
            else:
                pygame.draw.rect(surf, fg, rect.inflate(-max(1, pcw // 4), -max(1, pch // 4)))

        if hud_extra:
            surf.blit(
                self._font_hud.render(hud_extra, True, COLOR_HUD),
                (margin, margin + title_h),
            )

        if z_cut is not None and z_cut_mode in ("slice", "rear") and section.min_z <= z_cut <= section.max_z:
            row = z_cut - section.min_z
            py = oz_base - row * pch + pch // 2
            pygame.draw.line(
                surf,
                COLOR_SLICE_LINE,
                (margin, py),
                (self.panel_w - margin, py),
                2,
            )
        return surf


def blit_split(
    target: pygame.Surface,
    top_view: pygame.Surface,
    section_view: pygame.Surface,
    *,
    top_w: int | None = None,
) -> None:
    target.fill(COLOR_BG)
    tw = top_w or WINDOW_PX_W // 2
    target.blit(top_view, (0, 0), (0, 0, min(tw, top_view.get_width()), top_view.get_height()))
    target.blit(section_view, (tw, 0))
