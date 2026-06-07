"""Fixed iso-stencil character renderer for the editor (no zoom/pan/orbit)."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import pygame

from src.prototype.dia_scale.display_scale import DisplayPreset, PRESET_NORMAL
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel
from src.prototype.dia_scale.voxel_3d_renderer import _kind_colors, _rotate_xyz
from src.characters.editor_diagnostics import DiagnosticMarker, DiagnosticReport, analyze_voxels, compute_floor_z
from src.characters.editor_floor import (
    FloorGlyphCell,
    build_floor_patch,
    floor_iso_draw_map,
    floor_screen_offset,
    floor_solid_char_cells,
)
from src.characters.editor_lighting import EditorLighting, brightness_at, shade_from_brightness
from src.characters.editor_shading import (
    build_column_depth,
    build_floor_shadow,
    shade_color,
    shade_factor_for_voxel,
)
from src.render.iso_character_view import (
    EDITOR_FLOOR_TILES,
    PITCH_CHARACTER_DEG,
    YAW_DEFAULT_DEG,
    ZOOM_FIXED,
)

VoxelPos = tuple[int, int, int]


def floor_tile_range() -> range:
    """Tile indices for 5×5 floor (1 m), centered on anchor."""
    return range(EDITOR_FLOOR_TILES)


def floor_world_extent(cx0: float, cy0: float) -> tuple[float, float, float, float]:
    """Char-grid AABB of the 1 m floor patch (exclusive max)."""
    solid = floor_solid_char_cells(int(round(cx0)), int(round(cy0)))
    if not solid:
        return cx0, cy0, cx0, cy0
    xs = [c[0] for c in solid]
    ys = [c[1] for c in solid]
    return float(min(xs)), float(min(ys)), float(max(xs) + 1), float(max(ys) + 1)


@dataclass
class FixedViewCamera:
    """Locked camera for game-faithful editor preview."""

    yaw_deg: float = YAW_DEFAULT_DEG
    pitch_deg: float = PITCH_CHARACTER_DEG
    zoom: float = ZOOM_FIXED

    @property
    def yaw(self) -> float:
        return math.radians(self.yaw_deg)

    @property
    def pitch(self) -> float:
        return math.radians(self.pitch_deg)


@dataclass
class RenderResult:
    surface: pygame.Surface
    origin_x: int = 0
    origin_y: int = 0
    cell_w: int = 10
    cell_h: int = 16
    floor_z: int = 0
    projected: list[tuple[int, int, int, int, str, tuple, tuple, str, VoxelPos | None]] = field(default_factory=list)
    diagnostics: DiagnosticReport | None = None


class IsoCharacterRenderer:
    """Render character voxels at fixed pitch/yaw/zoom with iso floor reference."""

    def __init__(
        self,
        *,
        preset: DisplayPreset | None = None,
        panel_w: int = 800,
        panel_h: int = 800,
        hud_font_size: int = 11,
    ) -> None:
        self.preset = preset or PRESET_NORMAL
        self.panel_w = panel_w
        self.panel_h = panel_h
        self.camera = FixedViewCamera()
        self._font = pygame.font.SysFont("consolas", max(6, self.preset.cell_h - 2))
        self._font_hud = pygame.font.SysFont("consolas", hud_font_size)

    def set_preset(self, preset: DisplayPreset) -> None:
        self.preset = preset
        self._font = pygame.font.SysFont("consolas", max(6, preset.cell_h - 2))

    def reset_view(self) -> None:
        self.camera = FixedViewCamera()

    def _orbit_like(self) -> object:
        class _O:
            pass

        o = _O()
        o.yaw = self.camera.yaw
        o.pitch = self.camera.pitch
        o.roll = 0.0
        return o

    def _project_point(
        self,
        x: float,
        y: float,
        z: float,
        *,
        cx0: float,
        cy0: float,
        cz0: float,
        orbit: object,
        zoom: float,
    ) -> tuple[float, int, int]:
        rx, ry, rz = _rotate_xyz(x - cx0, y - cy0, z - cz0, orbit)  # type: ignore[arg-type]
        su = int(round(rx * zoom))
        sv = int(round(-rz * zoom))
        return ry, su, sv

    def _draw_floor_stamps(
        self,
        surf: pygame.Surface,
        *,
        floor_cells: list[FloorGlyphCell],
        feet_cx: int,
        feet_cy: int,
        ox: int,
        oy: int,
        cw: int,
        ch: int,
        lighting: EditorLighting,
        floor_shadow: set[tuple[int, int]],
        floor_seed: int = 0,
    ) -> None:
        """5×5 diag stamp floor on iso screen (row spans filled — no gaps)."""
        draw_map = floor_iso_draw_map(
            feet_cx, feet_cy, seed=floor_seed,
        )
        drawn_char: set[tuple[int, int]] = {
            floor_screen_offset(c.cx, c.cy, ref_cx=feet_cx, ref_cy=feet_cy)
            for c in floor_cells
        }
        for (su, sv), cell in draw_map.items():
            px = ox + su * cw
            py = oy + sv * ch
            b = brightness_at(float(cell.cx), float(cell.cy), 0.0, lighting=lighting, up_bias=1.0)
            if (cell.cx, cell.cy) in floor_shadow:
                b *= 0.55
            fg, bg = shade_from_brightness(cell.fg, cell.bg, b)
            rect = pygame.Rect(px, py, cw, ch)
            pygame.draw.rect(surf, bg, rect)
            if (su, sv) in drawn_char and cw >= 4 and ch >= 6 and cell.ch.strip():
                surf.blit(self._font.render(cell.ch, True, fg), (px, py))

    def _blink_on(self, *, freq: float = 3.5) -> bool:
        return int(time.monotonic() * freq) % 2 == 0

    def _draw_marker(
        self,
        surf: pygame.Surface,
        px: int,
        py: int,
        cw: int,
        ch: int,
        marker: DiagnosticMarker,
    ) -> None:
        if not self._blink_on():
            return
        if marker.glyph == "s":
            fg, bg = (220, 200, 40), (60, 50, 10)
        else:
            fg, bg = (255, 60, 60), (60, 10, 10)
        rect = pygame.Rect(px, py, cw, ch)
        pygame.draw.rect(surf, bg, rect)
        surf.blit(self._font.render(marker.glyph, True, fg), (px, py))

    def render(
        self,
        model: TreeVoxelModel,
        *,
        title: str = "",
        hud_lines: list[str] | None = None,
        kind_filter: set[str] | None = None,
        hidden_kinds: set[str] | None = None,
        highlight_kind: str | None = None,
        highlight_voxel: VoxelPos | None = None,
        show_floor: bool = True,
        walking: bool = False,
        show_diagnostics: bool = True,
        show_shading: bool = True,
        view_scale: int = 1,
        lighting: EditorLighting | None = None,
        floor_seed: int = 0,
    ) -> RenderResult:
        surf = pygame.Surface((self.panel_w, self.panel_h))
        surf.fill((14, 16, 24))
        scale = max(1, view_scale)
        cw = max(4, self.preset.cell_w * scale)
        ch = max(6, self.preset.cell_h * scale)
        glyph_px = max(6, ch - 2)
        if not hasattr(self, "_glyph_px") or self._glyph_px != glyph_px:
            self._font = pygame.font.SysFont("consolas", glyph_px)
            self._glyph_px = glyph_px
        margin = 8
        title_h = self._font_hud.get_height() + 4 if title else 0
        hud_rows = len(hud_lines or [])
        bottom_h = max(4, hud_rows * (self._font_hud.get_height() + 2))
        avail_w = self.panel_w - margin * 2
        avail_h = self.panel_h - margin * 2 - title_h - bottom_h

        floor_z = compute_floor_z(model.voxels)
        cx0 = float(model.anchor_x)
        cy0 = float(model.anchor_y)
        cz0 = float(floor_z)
        orbit = self._orbit_like()
        zoom = self.camera.zoom
        lit = lighting or EditorLighting()

        feet_cx = int(round(cx0))
        feet_cy = int(round(cy0))
        floor_cells = build_floor_patch(feet_cx, feet_cy, seed=floor_seed) if show_floor else []

        diag = analyze_voxels(model.voxels, walking=walking, floor_z=floor_z) if show_diagnostics else None
        col_depth = build_column_depth(model.voxels) if show_shading else {}
        floor_shadow = build_floor_shadow(model.voxels, floor_z) if show_shading else set()

        projected_raw: list[tuple[float, int, int, str, tuple, tuple, str, VoxelPos]] = []
        floor_proj: list[tuple[int, int]] = []
        if floor_cells:
            for cell in floor_cells:
                floor_proj.append(
                    floor_screen_offset(
                        cell.cx, cell.cy,
                        ref_cx=feet_cx, ref_cy=feet_cy,
                    )
                )

        for (x, y, z), kind in model.voxels.items():
            if kind_filter is not None and kind not in kind_filter:
                continue
            if hidden_kinds and kind in hidden_kinds:
                continue
            depth, su, sv = self._project_point(x, y, z, cx0=cx0, cy0=cy0, cz0=cz0, orbit=orbit, zoom=zoom)
            fg, bg, ch_char = _kind_colors().get(kind, ((200, 200, 200), (30, 30, 30), "?"))
            if show_shading:
                col = shade_factor_for_voxel(
                    (x, y, z), kind, column_depth=col_depth, voxels=model.voxels,
                )
                b = brightness_at(float(x), float(y), float(z), lighting=lit, up_bias=0.85)
                sf = col + (1.0 - b) * 0.5
                fg, bg = shade_color(fg, bg, min(0.92, sf))
            if highlight_kind and kind == highlight_kind:
                fg = tuple(min(255, c + 40) for c in fg)
            sel = (x, y, z) == highlight_voxel if highlight_voxel else False
            if sel:
                fg = tuple(min(255, c + 80) for c in fg)
                bg = tuple(min(255, c + 30) for c in bg)
            projected_raw.append((depth, su, sv, ch_char, fg, bg, kind, (x, y, z)))

        result = RenderResult(surface=surf, cell_w=cw, cell_h=ch, floor_z=floor_z, diagnostics=diag)
        oy = margin + title_h

        if projected_raw or show_floor:
            all_su = [p[1] for p in projected_raw]
            all_sv = [p[2] for p in projected_raw]
            if floor_proj:
                all_su.extend(su for su, _sv in floor_proj)
                all_sv.extend(sv for _su, sv in floor_proj)
            min_u = min(all_su) if all_su else -EDITOR_FLOOR_TILES
            max_u = max(all_su) if all_su else EDITOR_FLOOR_TILES
            min_v = min(all_sv) if all_sv else -EDITOR_FLOOR_TILES
            max_v = max(all_sv) if all_sv else EDITOR_FLOOR_TILES
            span_u = max(1, max_u - min_u + 1)
            span_v = max(1, max_v - min_v + 1)
            ox = margin + (avail_w - span_u * cw) // 2 - min_u * cw
            oy = margin + title_h + (avail_h - span_v * ch) // 2 - min_v * ch
            result.origin_x = ox
            result.origin_y = oy

            if show_floor and floor_cells:
                self._draw_floor_stamps(
                    surf,
                    floor_cells=floor_cells,
                    feet_cx=feet_cx,
                    feet_cy=feet_cy,
                    ox=ox,
                    oy=oy,
                    cw=cw,
                    ch=ch,
                    lighting=lit,
                    floor_shadow=floor_shadow,
                    floor_seed=floor_seed,
                )

            projected_raw.sort(key=lambda t: (t[0], t[2], t[1]))
            for depth, su, sv, ch_char, fg, bg, kind, vpos in projected_raw:
                px = ox + su * cw
                py = oy + sv * ch
                rect = pygame.Rect(px, py, cw, ch)
                pygame.draw.rect(surf, bg, rect)
                if cw >= 4 and ch >= 6:
                    surf.blit(self._font.render(ch_char, True, fg), (px, py))
                else:
                    pygame.draw.rect(surf, fg, rect.inflate(-max(1, cw // 4), -max(1, ch // 4)))
                if highlight_voxel and vpos == highlight_voxel:
                    pygame.draw.rect(surf, (255, 220, 80), rect, 2)
                result.projected.append((px, py, su, sv, ch_char, fg, bg, kind, vpos))

            if diag and show_diagnostics:
                for marker in diag.markers:
                    _, su, sv = self._project_point(
                        marker.x, marker.y, marker.z,
                        cx0=cx0, cy0=cy0, cz0=cz0, orbit=orbit, zoom=zoom,
                    )
                    px = ox + su * cw
                    py = oy + sv * ch
                    self._draw_marker(surf, px, py, cw, ch, marker)
        else:
            surf.blit(self._font_hud.render("empty view", True, (140, 145, 160)), (margin, margin + title_h))

        if title:
            surf.blit(self._font_hud.render(title, True, (140, 145, 160)), (margin, margin))
        y = self.panel_h - bottom_h + 4
        for line in hud_lines or []:
            surf.blit(self._font_hud.render(line, True, (140, 145, 160)), (margin, y))
            y += self._font_hud.get_height() + 2

        result.surface = surf
        return result

    def pick_voxel(
        self,
        model: TreeVoxelModel,
        mx: int,
        my: int,
        render_result: RenderResult,
        *,
        kind_filter: set[str] | None = None,
        hidden_kinds: set[str] | None = None,
    ) -> VoxelPos | None:
        """Return model voxel (x,y,z) at screen pixel, front-most."""
        for px, py, _su, _sv, _ch, _fg, _bg, _kind, vpos in reversed(render_result.projected):
            cw, ch = render_result.cell_w, render_result.cell_h
            if vpos is None:
                continue
            if px <= mx < px + cw and py <= my < py + ch:
                return vpos
        return None

    def pick_empty_cell(
        self,
        mx: int,
        my: int,
        render_result: RenderResult,
        *,
        floor_z: int,
        anchor_x: int,
        anchor_y: int,
    ) -> VoxelPos:
        """Approximate empty cell from click on view (uses screen cell → model XY, floor Z)."""
        cw, ch = render_result.cell_w, render_result.cell_h
        ox, oy = render_result.origin_x, render_result.origin_y
        su = int(round((mx - ox) / max(1, cw)))
        sv = int(round((my - oy) / max(1, ch)))
        # Inverse projection rough: use anchor + screen offset as XY hint
        return (anchor_x + su, anchor_y - sv, floor_z + 1)

