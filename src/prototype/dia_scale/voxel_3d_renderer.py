"""3D orthographic voxel tree view with euler orbit."""
from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from src.prototype.dia_scale.constants import (
    COLOR_BRANCH_BG,
    COLOR_BRANCH_FG,
    COLOR_CANOPY_BG,
    COLOR_CANOPY_FG,
    COLOR_HUD,
    COLOR_SECTION_BG,
    COLOR_TRUNK_BG,
    COLOR_TRUNK_FG,
    VOXEL_BRANCH,
    VOXEL_LEAF,
    VOXEL_TRUNK,
)
from src.prototype.dia_scale.display_scale import DisplayPreset, WINDOW_PX_H, WINDOW_PX_W
from src.prototype.dia_scale.slice_view import SliceViewMode
from src.prototype.dia_scale.tree_voxel_gen import TreeVoxelModel

def _kind_colors() -> dict[str, tuple[tuple, tuple, str]]:
    from src.characters.loader import load_palette
    from src.characters.voxel_kinds import kind_glyph

    base = {
        VOXEL_TRUNK: (COLOR_TRUNK_FG, COLOR_TRUNK_BG, "T"),
        VOXEL_BRANCH: (COLOR_BRANCH_FG, COLOR_BRANCH_BG, "|"),
        VOXEL_LEAF: (COLOR_CANOPY_FG, COLOR_CANOPY_BG, "Y"),
        "skin": ((255, 220, 190), (40, 30, 28), kind_glyph("skin")),
        "skin_ghost": ((230, 235, 245), (35, 38, 48), kind_glyph("skin_ghost")),
        "body_head": ((255, 210, 175), (45, 32, 28), kind_glyph("body_head")),
        "body_torso": ((230, 175, 130), (38, 28, 22), kind_glyph("body_torso")),
        "body_arm_l": ((120, 180, 255), (22, 38, 58), kind_glyph("body_arm_l")),
        "body_arm_r": ((255, 160, 110), (48, 28, 18), kind_glyph("body_arm_r")),
        "body_leg_l": ((100, 210, 140), (18, 38, 26), kind_glyph("body_leg_l")),
        "body_leg_r": ((180, 220, 100), (32, 42, 18), kind_glyph("body_leg_r")),
        "hair": ((90, 60, 35), (20, 14, 10), kind_glyph("hair")),
        "scalp": ((255, 220, 190), (40, 30, 28), kind_glyph("scalp")),
        "eye": ((80, 130, 200), (18, 28, 40), kind_glyph("eye")),
        "feature": ((120, 120, 130), (28, 28, 32), kind_glyph("feature")),
        "weapon": ((180, 185, 195), (40, 42, 48), kind_glyph("weapon")),
        "armor_chest": ((160, 155, 150), (35, 32, 30), kind_glyph("armor_chest")),
        "armor_legs": ((100, 80, 55), (28, 22, 16), kind_glyph("armor_legs")),
        "armor_head": ((160, 155, 150), (35, 32, 30), kind_glyph("armor_head")),
        "lantern": ((255, 200, 80), (50, 35, 10), kind_glyph("lantern")),
        "amulet": ((255, 230, 100), (40, 35, 15), kind_glyph("amulet")),
    }
    try:
        pal = load_palette()
        for kind, (fg, bg, ch) in list(base.items()):
            if kind in pal:
                entry = pal[kind]
                base[kind] = (tuple(entry["fg"]), tuple(entry["bg"]), ch)
    except Exception:
        pass
    return base


@dataclass
class Orbit3D:
    """Euler orbit in radians: yaw(Z), pitch(X), roll(Y)."""

    yaw: float = math.radians(30.0)
    pitch: float = math.radians(-18.0)
    roll: float = 0.0
    pan_u: float = 0.0
    pan_v: float = 0.0
    zoom: float = 2.4

    def rotate_drag(self, dx: float, dy: float) -> None:
        s = 0.006
        self.yaw += dx * s
        self.pitch += dy * s
        self.roll += (dx - dy) * s * 0.45

    def pan_pixels(self, dpx: float, dpy: float) -> None:
        self.pan_u += dpx
        self.pan_v += dpy

    def zoom_wheel(self, steps: int) -> None:
        self.zoom = max(0.6, min(8.0, self.zoom * (1.12**steps)))


def _rotate_xyz(x: float, y: float, z: float, orbit: Orbit3D) -> tuple[float, float, float]:
    cz, sz = math.cos(orbit.yaw), math.sin(orbit.yaw)
    x1 = x * cz - y * sz
    y1 = x * sz + y * cz
    z1 = z

    cx, sx = math.cos(orbit.pitch), math.sin(orbit.pitch)
    x2 = x1
    y2 = y1 * cx - z1 * sx
    z2 = y1 * sx + z1 * cx

    cy, sy = math.cos(orbit.roll), math.sin(orbit.roll)
    x3 = x2 * cy + z2 * sy
    y3 = y2
    z3 = -x2 * sy + z2 * cy
    return x3, y3, z3


def _voxel_visible(
    x: int,
    y: int,
    z: int,
    *,
    slice_view: SliceViewMode,
    section_plane: str,
    section_coord: int,
    top_slice_z: int,
) -> bool:
    if slice_view == "off":
        return True
    if slice_view == "rear" and z > top_slice_z:
        return False
    if slice_view == "slice":
        if section_plane == "yz":
            return x == section_coord
        return y == section_coord
    return True


class Voxel3DRenderer:
    def __init__(
        self,
        *,
        preset: DisplayPreset,
        panel_w: int | None = None,
        panel_h: int | None = None,
        hud_font_size: int = 9,
    ) -> None:
        self.preset = preset
        self.panel_w = panel_w or WINDOW_PX_W
        self.panel_h = panel_h or WINDOW_PX_H
        self.hud_font_size = hud_font_size
        self.orbit = Orbit3D()
        self._font = pygame.font.SysFont("consolas", max(6, preset.cell_h - 2))
        self._font_hud = pygame.font.SysFont("consolas", hud_font_size)

    def set_preset(self, preset: DisplayPreset) -> None:
        self.preset = preset
        self._font = pygame.font.SysFont("consolas", max(6, preset.cell_h - 2))
        self._font_hud = pygame.font.SysFont("consolas", self.hud_font_size)

    def reset_view(self) -> None:
        self.orbit = Orbit3D()

    def render(
        self,
        model: TreeVoxelModel,
        *,
        title: str,
        hud_lines: list[str] | None = None,
        slice_view: SliceViewMode = "off",
        section_plane: str = "yz",
        section_coord: int = 0,
        top_slice_z: int = 0,
    ) -> pygame.Surface:
        surf = pygame.Surface((self.panel_w, self.panel_h))
        surf.fill(COLOR_SECTION_BG)
        cw, ch = self.preset.cell_w, self.preset.cell_h
        margin = 8
        title_h = self._font_hud.get_height() + 4
        hud_rows = len(hud_lines or [])
        bottom_h = max(
            self._font_hud.get_height() * 3,
            hud_rows * (self._font_hud.get_height() + 4) + margin,
        )
        avail_w = self.panel_w - margin * 2
        avail_h = self.panel_h - margin * 2 - title_h - bottom_h

        cx0 = float(model.anchor_x)
        cy0 = float(model.anchor_y)
        cz0 = model.max_z() * 0.5

        projected: list[tuple[float, int, int, str, tuple, tuple, str]] = []
        for (x, y, z), kind in model.voxels.items():
            if not _voxel_visible(
                x,
                y,
                z,
                slice_view=slice_view,
                section_plane=section_plane,
                section_coord=section_coord,
                top_slice_z=top_slice_z,
            ):
                continue
            rx, ry, rz = _rotate_xyz(x - cx0, y - cy0, z - cz0, self.orbit)
            su = rx * self.orbit.zoom + self.orbit.pan_u
            sv = -rz * self.orbit.zoom + self.orbit.pan_v
            fg, bg, ch_char = _kind_colors().get(kind, ((200, 200, 200), (30, 30, 30), "?"))
            projected.append(
                (ry, int(round(su)), int(round(sv)), ch_char, fg, bg, kind)
            )

        pcw, pch = cw, ch
        oy = margin + title_h
        if projected:
            min_u = min(p[1] for p in projected)
            max_u = max(p[1] for p in projected)
            min_v = min(p[2] for p in projected)
            max_v = max(p[2] for p in projected)
            span_u = max(1, max_u - min_u + 1)
            span_v = max(1, max_v - min_v + 1)
            scale = min(avail_w // (span_u * cw), avail_h // (span_v * ch), 2)
            if scale < 1:
                scale = 1
            pcw, pch = cw * scale, ch * scale
            ox = margin + (avail_w - span_u * pcw) // 2 - min_u * pcw
            oy = margin + title_h + (avail_h - span_v * pch) // 2 - min_v * pch

            projected.sort(key=lambda t: (t[0], t[2], t[1]))
            for _depth, u, v, ch_char, fg, bg, _kind in projected:
                px = ox + u * pcw
                py = oy + v * pch
                rect = pygame.Rect(px, py, pcw, pch)
                pygame.draw.rect(surf, bg, rect)
                if pcw >= 4 and pch >= 6:
                    surf.blit(self._font.render(ch_char, True, fg), (px, py))
                else:
                    pygame.draw.rect(surf, fg, rect.inflate(-max(1, pcw // 4), -max(1, pch // 4)))
        else:
            surf.blit(self._font_hud.render("empty view", True, COLOR_HUD), (margin, margin + title_h))

        surf.blit(self._font_hud.render(title, True, COLOR_HUD), (margin, margin))
        y = self.panel_h - bottom_h + 4
        for line in hud_lines or []:
            surf.blit(self._font_hud.render(line, True, COLOR_HUD), (margin, y))
            y += self._font_hud.get_height() + 4

        return surf
