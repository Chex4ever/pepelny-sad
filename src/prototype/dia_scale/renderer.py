"""CPU renderer with camera rotation and fixed-window presets (diag iso stamp storage)."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.prototype.dia_scale.constants import (
    COLOR_BG,
    COLOR_HUD,
    COLOR_SLICE_LINE,
    PLAYER_HEIGHT_TILES,
    TILES_PER_M_XY,
    TILES_PER_M_Z,
    VOXEL_BRANCH,
    VOXEL_LEAF,
    VOXEL_TRUNK,
)
from src.prototype.dia_scale.display_scale import (
    HUD_ROWS,
    PRESET_NORMAL,
    DisplayPreset,
    WINDOW_PX_H,
    WINDOW_PX_W,
    visible_chars,
)
from src.prototype.dia_scale.tessellation import analyze_floor_coverage, rotate_offset, world_to_view
from src.prototype.dia_scale.world_grid import GridSolid, WorldGrid

_VOXEL_KINDS = frozenset({VOXEL_TRUNK, VOXEL_BRANCH, VOXEL_LEAF})


@dataclass
class Camera:
    focus_cx: int = 0
    focus_cy: int = 0
    rotation: int = 0

    def pan(self, dx: int, dy: int) -> None:
        self.focus_cx += dx
        self.focus_cy += dy

    def pan_pixels(self, dpx: int, dpy: int, *, cell_w: int, cell_h: int) -> None:
        """Drag-to-pan: screen delta in px → world focus shift (respects rotation)."""
        if dpx == 0 and dpy == 0:
            return
        dvx = -int(round(dpx / cell_w)) if cell_w else 0
        dvy = -int(round(dpy / cell_h)) if cell_h else 0
        if dvx == 0 and dvy == 0:
            if abs(dpx) >= cell_w // 2:
                dvx = -1 if dpx > 0 else 1
            elif abs(dpy) >= cell_h // 2:
                dvy = -1 if dpy > 0 else 1
        if dvx == 0 and dvy == 0:
            return
        wx, wy = rotate_offset(dvx, dvy, (4 - self.rotation) % 4)
        self.pan(wx, wy)

    def rotate_cw(self) -> None:
        self.rotation = (self.rotation + 1) % 4

    def rotate_ccw(self) -> None:
        self.rotation = (self.rotation - 1) % 4


class CharGridRenderer:
    def __init__(self, *, preset: DisplayPreset | None = None) -> None:
        self.preset = preset or PRESET_NORMAL
        self.camera = Camera()
        self._rebuild_fonts()
        self.surface = pygame.Surface((WINDOW_PX_W, WINDOW_PX_H))

    def set_preset(self, preset: DisplayPreset) -> None:
        if preset.cell_w == self.preset.cell_w and preset.cell_h == self.preset.cell_h:
            return
        self.preset = preset
        self._rebuild_fonts()

    def _rebuild_fonts(self) -> None:
        ch = self.preset.cell_h
        self._font = pygame.font.SysFont("consolas", max(6, ch - 2))
        self._font_hud = pygame.font.SysFont("consolas", 9)

    @property
    def width(self) -> int:
        return WINDOW_PX_W

    @property
    def height(self) -> int:
        return WINDOW_PX_H

    def map_band_height(self) -> int:
        return WINDOW_PX_H - HUD_ROWS * 14 - 8

    def top_panel_width(self, *, split_section: bool) -> int:
        return WINDOW_PX_W // 2 if split_section else WINDOW_PX_W

    def point_in_map(self, mx: int, my: int, *, split_section: bool) -> bool:
        if my < 0 or my >= self.map_band_height():
            return False
        if mx < 0 or mx >= self.top_panel_width(split_section=split_section):
            return False
        return True

    def _view_half(self, viewport_w: int | None = None) -> tuple[int, int]:
        vw, vh = visible_chars(self.preset, viewport_w)
        return vw // 2, vh // 2

    def _view_to_pixel(
        self,
        vx: int,
        vy: int,
        *,
        viewport_w: int | None = None,
        viewport_cx: int | None = None,
    ) -> tuple[int, int]:
        cw, ch = self.preset.cell_w, self.preset.cell_h
        map_h = self.map_band_height()
        vpx_w = viewport_w or WINDOW_PX_W
        center_x = viewport_cx if viewport_cx is not None else vpx_w // 2
        px = center_x + vx * cw
        py = map_h // 2 + vy * ch
        return px, py

    def _draw_cell(
        self,
        px: int,
        py: int,
        ch_char: str,
        fg: tuple[int, int, int],
        bg: tuple[int, int, int],
    ) -> None:
        cw, ch = self.preset.cell_w, self.preset.cell_h
        px -= cw // 2
        py -= ch // 2
        cell = pygame.Surface((cw, ch))
        cell.fill(bg)
        text = self._font.render(ch_char, True, fg)
        cell.blit(text, (0, 0))
        self.surface.blit(cell, (px, py))

    def _draw_world_cut_line(
        self,
        cam: Camera,
        w0: tuple[int, int],
        w1: tuple[int, int],
        *,
        viewport_w: int,
        viewport_cx: int,
    ) -> None:
        v0 = world_to_view(w0[0], w0[1], cam.focus_cx, cam.focus_cy, cam.rotation)
        v1 = world_to_view(w1[0], w1[1], cam.focus_cx, cam.focus_cy, cam.rotation)
        p0 = self._view_to_pixel(v0[0], v0[1], viewport_w=viewport_w, viewport_cx=viewport_cx)
        p1 = self._view_to_pixel(v1[0], v1[1], viewport_w=viewport_w, viewport_cx=viewport_cx)
        pygame.draw.line(self.surface, COLOR_SLICE_LINE, p0, p1, 2)

    def render(
        self,
        grid: WorldGrid,
        *,
        hud_lines: list[str] | None = None,
        viewport_w: int | None = None,
        viewport_cx: int | None = None,
        z_cut: int | None = None,
        z_cut_solids: list[GridSolid] | None = None,
        section_cut: tuple[str, int] | None = None,
    ) -> pygame.Surface:
        from src.prototype.dia_scale.cross_section import section_plane_world_line

        self.surface.fill(COLOR_BG)
        cam = self.camera
        cw, ch = self.preset.cell_w, self.preset.cell_h
        vpx_w = viewport_w or WINDOW_PX_W
        vpx_cx = viewport_cx if viewport_cx is not None else vpx_w // 2
        half_w, half_h = self._view_half(vpx_w)

        draw_solids = grid.solids
        if z_cut is not None:
            draw_solids = [s for s in grid.solids if s.kind not in _VOXEL_KINDS]
            if z_cut_solids is not None:
                draw_solids = list(draw_solids) + list(z_cut_solids)

        for _sort, cx, cy, ch_char, fg, bg, _layer in grid.all_draw_cells():
            if _layer != "floor":
                continue
            vx, vy = world_to_view(cx, cy, cam.focus_cx, cam.focus_cy, cam.rotation)
            if abs(vx) > half_w or abs(vy) > half_h:
                continue
            px, py = self._view_to_pixel(vx, vy, viewport_w=vpx_w, viewport_cx=vpx_cx)
            self._draw_cell(px, py, ch_char, fg, bg)

        solid_items: list[tuple[float, int, int, str, tuple, tuple, str]] = []
        for s in draw_solids:
            solid_items.append((float(s.cy) + s.z_max * 0.01, s.cx, s.cy, s.ch, s.fg, s.bg, s.kind))
        for ent in grid.entities:
            for cx, cy, ch_char, fg, bg in ent.cells:
                solid_items.append((float(cy) + ent.z_sort, cx, cy, ch_char, fg, bg, ent.entity_id))
        solid_items.sort(key=lambda t: (t[0], t[2], t[1]))

        for _sort, cx, cy, ch_char, fg, bg, _layer in solid_items:
            vx, vy = world_to_view(cx, cy, cam.focus_cx, cam.focus_cy, cam.rotation)
            if abs(vx) > half_w or abs(vy) > half_h:
                continue
            px, py = self._view_to_pixel(vx, vy, viewport_w=vpx_w, viewport_cx=vpx_cx)
            self._draw_cell(px, py, ch_char, fg, bg)

        if section_cut is not None:
            plane, coord = section_cut
            w0, w1 = section_plane_world_line(
                plane, coord, focus_cx=cam.focus_cx, focus_cy=cam.focus_cy
            )
            self._draw_world_cut_line(cam, w0, w1, viewport_w=vpx_w, viewport_cx=vpx_cx)

        y = WINDOW_PX_H - HUD_ROWS * 14
        lines = hud_lines or []
        for line in lines[:HUD_ROWS + 2]:
            self.surface.blit(self._font_hud.render(line, True, COLOR_HUD), (4, y))
            y += self._font_hud.get_height() + 2
        return self.surface

    def default_hud(self, grid: WorldGrid) -> list[str]:
        from src.prototype.dia_scale.constants import ROTATION_LABELS

        nx = grid.meta.get("nx", 0)
        ny = grid.meta.get("ny", 0)
        cov = analyze_floor_coverage(nx, ny) if nx and ny else None
        rot = ROTATION_LABELS[self.camera.rotation % 4]
        vw, vh = visible_chars(self.preset)
        line1 = (
            f"test_2x1_dia | xy={TILES_PER_M_XY}/m z={TILES_PER_M_Z}/m | "
            f"player {PLAYER_HEIGHT_TILES}z | {self.preset.label} view {vw}x{vh}"
        )
        line2 = (
            f"cam {rot} focus=({self.camera.focus_cx},{self.camera.focus_cy}) "
            f"seed={grid.meta.get('seed', '?')}"
        )
        if cov:
            line2 += f" | floor cover={cov.coverage_pct:.0f}% seams={cov.seams}"
        if grid.meta.get("voxel_tree"):
            vt = grid.meta["voxel_tree"]
            line2 += f" | tree h={vt.get('height', '?')} branches={vt.get('branches', 0)}"
        return [line1, line2]
