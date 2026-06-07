"""Bake tile stencils into a GPU texture atlas."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.constants import CELL_H, CELL_W, COLOR_BG, ISO_STEP_X, ISO_STEP_Y
from src.render.gpu.font_util import ui_font
from src.render.gpu.texture_upload import surface_rgba_bytes
from src.render.tile_stencil import CHAR_STENCIL, load_tile_stencil


@dataclass(frozen=True)
class AtlasRegion:
    u0: float
    v0: float
    u1: float
    v1: float
    anchor_dx: int
    anchor_dy: int
    pixel_w: int
    pixel_h: int


def preload_stencil_ids() -> list[str]:
    """Stencil ids to bake once at GPU init."""
    ids: set[str] = set(CHAR_STENCIL.values())
    ids.update(
        {
            "grass",
            "grass_dry",
            "ridge",
            "ruins",
            "road",
            "tree",
            "wall",
            "herb",
            "shard",
            "water",
            "loot",
            "forge",
            "elder_station",
            "stairs_down",
            "stairs_up",
            "battle",
            "trigger",
            "torch",
            "floor",
            "iso_tile_fill",
        }
    )
    try:
        from src.data.art_loader import load_biomes

        for biome in load_biomes().values():
            sid = biome.get("stencil_id")
            if sid:
                ids.add(sid)
            for key in (
                "floor_variants",
                "grass_overlay_variants",
                "bush_variants",
                "transition_stencil_id",
            ):
                val = biome.get(key)
                if isinstance(val, str) and val:
                    ids.add(val)
                elif isinstance(val, list):
                    ids.update(val)
    except Exception:
        pass
    return sorted(ids)


def opaque_splat_stencil_ids() -> list[str]:
    """Floor stencils that get a pre-baked opaque diamond region (splat:id)."""
    return preload_stencil_ids()


# Local char anchor when baking splat:* — room for iso footprint diamond in slot.
_OPAQUE_SPLAT_ANCHOR_CX = ISO_STEP_X + 3
_OPAQUE_SPLAT_ANCHOR_CY = ISO_STEP_Y + 4


class TileAtlas:
    """Single texture atlas; regions keyed by stencil_id."""

    PAD = 2
    SLOT_W = 14 * CELL_W
    SLOT_H = 10 * CELL_H

    def __init__(self, ctx):
        self._ctx = ctx
        self._regions: dict[str, AtlasRegion] = {}
        self._cols = 16
        self._texture = None
        self._size = 4096
        self._sheet = pygame.Surface((self._size, self._size), pygame.SRCALPHA)
        self._sheet.fill((*COLOR_BG, 255))
        self._next_slot = 0
        self._dirty_rects: list[tuple[int, int, int, int]] = []

    @property
    def texture_size(self) -> int:
        return self._size

    def region_count(self) -> int:
        return len(self._regions)

    def preload(self, stencil_ids: list[str] | None = None) -> None:
        for sid in stencil_ids or preload_stencil_ids():
            self.get_region(sid)
        for sid in ("sprite:player", "sprite:companion"):
            try:
                self.get_region(sid)
            except Exception:
                pass
        self.preload_procedural_trees()
        self.preload_opaque_floor_splats()
        self.ensure_texture()

    def preload_opaque_floor_splats(self) -> None:
        """Bake splat:id — footprint bg + glyphs opaque (1 GPU quad, no runtime undercoat)."""
        for sid in opaque_splat_stencil_ids():
            self.get_region(f"splat:{sid}")

    def preload_procedural_trees(self) -> None:
        """Bake parametric tree stencils once (avoid atlas work during gpu_map)."""
        for variant in range(6):
            for height in range(3, 11):
                for radius in range(1, 4):
                    self.get_region(f"tree_canopy_v{variant}_h{height}_r{radius}")
        for sid in ("tree_trunk_slim", "tree_trunk_thick"):
            self.get_region(sid)

    def get_region(self, stencil_id: str) -> AtlasRegion:
        reg = self._regions.get(stencil_id)
        if reg is None:
            reg = self._bake(stencil_id)
        return reg

    def _bake(self, stencil_id: str) -> AtlasRegion:
        if stencil_id.startswith("splat:"):
            return self._bake_opaque_floor_splat(stencil_id[6:])
        if stencil_id.startswith("sprite:"):
            from src.render.tile_stencil import load_sprite

            stencil = load_sprite(stencil_id.split(":", 1)[1])
        else:
            stencil = load_tile_stencil(stencil_id)
        slot = self._next_slot
        self._next_slot += 1
        col = slot % self._cols
        row = slot // self._cols
        ox = col * self.SLOT_W + self.PAD
        oy = row * self.SLOT_H + self.PAD
        min_dx = min((g.dx for g in stencil.glyphs), default=0)
        min_dy = min((g.dy for g in stencil.glyphs), default=0)
        max_dx = max((g.dx for g in stencil.glyphs), default=0)
        max_dy = max((g.dy for g in stencil.glyphs), default=0)
        pw = (max_dx - min_dx + 1) * CELL_W
        ph = (max_dy - min_dy + 1) * CELL_H
        cell = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
        for g in stencil.glyphs:
            px = ox + (g.dx - min_dx) * CELL_W
            py = oy + (g.dy - min_dy) * CELL_H
            cell.fill((*stencil.default_bg, 255))
            cell.blit(ui_font().render(g.ch, True, stencil.default_fg), (0, 0))
            self._sheet.blit(cell, (px, py))
        u0 = ox / self._size
        u1 = (ox + pw) / self._size
        v_top = 1.0 - oy / self._size
        v_bottom = 1.0 - (oy + ph) / self._size
        reg = AtlasRegion(u0, v_bottom, u1, v_top, min_dx, min_dy, pw, ph)
        self._regions[stencil_id] = reg
        self._dirty_rects.append((ox, oy, pw, ph))
        return reg

    def _bake_opaque_floor_splat(self, base_id: str) -> AtlasRegion:
        """Opaque iso footprint + stencil glyphs — matches CPU fill_iso_footprint + stamp."""
        from src.render.iso_footprint import iso_footprint_cells

        stencil = load_tile_stencil(base_id)
        ax, ay = _OPAQUE_SPLAT_ANCHOR_CX, _OPAQUE_SPLAT_ANCHOR_CY
        cells = iso_footprint_cells(ax, ay)
        min_cx = min(c[0] for c in cells)
        min_cy = min(c[1] for c in cells)
        max_cx = max(c[0] for c in cells)
        max_cy = max(c[1] for c in cells)
        pw = (max_cx - min_cx + 1) * CELL_W
        ph = (max_cy - min_cy + 1) * CELL_H

        slot = self._next_slot
        self._next_slot += 1
        col = slot % self._cols
        row = slot // self._cols
        ox = col * self.SLOT_W + self.PAD
        oy = row * self.SLOT_H + self.PAD

        patch = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg = (*stencil.default_bg, 255)
        patch.fill(bg)
        cell = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
        font = ui_font()
        for cx, cy in cells:
            lx = (cx - min_cx) * CELL_W
            ly = (cy - min_cy) * CELL_H
            cell.fill(bg)
            patch.blit(cell, (lx, ly))
        min_dx = min((g.dx for g in stencil.glyphs), default=0)
        min_dy = min((g.dy for g in stencil.glyphs), default=0)
        for g in stencil.glyphs:
            lx = (ax + g.dx - min_cx) * CELL_W
            ly = (ay + g.dy - min_cy) * CELL_H
            cell.fill(bg)
            cell.blit(font.render(g.ch, True, stencil.default_fg), (0, 0))
            patch.blit(cell, (lx, ly))

        self._sheet.blit(patch, (ox, oy))
        u0 = ox / self._size
        u1 = (ox + pw) / self._size
        v_top = 1.0 - oy / self._size
        v_bottom = 1.0 - (oy + ph) / self._size
        reg = AtlasRegion(u0, v_bottom, u1, v_top, min_dx, min_dy, pw, ph)
        self._regions[f"splat:{base_id}"] = reg
        self._dirty_rects.append((ox, oy, pw, ph))
        return reg

    def _upload_rect(self, ox: int, oy: int, pw: int, ph: int) -> None:
        if self._texture is None:
            return
        sub = self._sheet.subsurface(pygame.Rect(ox, oy, pw, ph))
        data = surface_rgba_bytes(sub)
        gl_y = self._size - oy - ph
        self._texture.write(data, viewport=(ox, gl_y, pw, ph))

    def ensure_texture(self):
        if self._texture is None:
            data = surface_rgba_bytes(self._sheet)
            self._texture = self._ctx.texture((self._size, self._size), 4, data)
            self._texture.filter = (self._ctx.NEAREST, self._ctx.NEAREST)
            self._dirty_rects.clear()
            return self._texture
        for ox, oy, pw, ph in self._dirty_rects:
            self._upload_rect(ox, oy, pw, ph)
        self._dirty_rects.clear()
        return self._texture

    @property
    def texture(self):
        return self.ensure_texture()

    def release(self) -> None:
        if self._texture is not None:
            self._texture.release()
            self._texture = None
