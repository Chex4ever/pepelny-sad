"""GPU texture atlas for UI glyphs (ASCII + Cyrillic, runtime bake)."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.constants import CELL_H, CELL_W
from src.render.gpu.font_util import static_ui_characters, ui_font
from src.render.gpu.texture_upload import surface_rgba_bytes


@dataclass(frozen=True)
class GlyphRegion:
    u0: float
    v0: float
    u1: float
    v1: float


class GlyphAtlas:
    COLS = 32
    ROWS = 16

    def __init__(self, ctx):
        self._ctx = ctx
        self._cw = CELL_W
        self._ch = CELL_H
        self._tex_w = self.COLS * self._cw
        self._tex_h = self.ROWS * self._ch
        self._regions: dict[str, GlyphRegion] = {}
        self._sheet = pygame.Surface((self._tex_w, self._tex_h), pygame.SRCALPHA)
        self._sheet.fill((0, 0, 0, 0))
        self._font = ui_font()
        self._next_slot = 0
        self._dirty_rects: list[tuple[int, int, int, int]] = []
        self._texture = None
        for ch in static_ui_characters():
            self._bake(ch)
        if "?" not in self._regions:
            self._bake("?")
        self._flush_texture()

    def _slot_origin(self, slot: int) -> tuple[int, int]:
        col = slot % self.COLS
        row = slot // self.COLS
        return col * self._cw, row * self._ch

    def _bake(self, ch: str) -> GlyphRegion | None:
        if ch in self._regions:
            return self._regions[ch]
        if self._next_slot >= self.COLS * self.ROWS:
            return self._regions.get("?")
        slot = self._next_slot
        self._next_slot += 1
        ox, oy = self._slot_origin(slot)
        glyph = self._font.render(ch, True, (255, 255, 255))
        self._sheet.fill((0, 0, 0, 0), pygame.Rect(ox, oy, self._cw, self._ch))
        self._sheet.blit(glyph, (ox, oy))
        u0 = ox / self._tex_w
        u1 = (ox + self._cw) / self._tex_w
        v_top = 1.0 - oy / self._tex_h
        v_bottom = 1.0 - (oy + self._ch) / self._tex_h
        reg = GlyphRegion(u0, v_bottom, u1, v_top)
        self._regions[ch] = reg
        self._dirty_rects.append((ox, oy, self._cw, self._ch))
        return reg

    def _upload_rect(self, ox: int, oy: int, pw: int, ph: int) -> None:
        if self._texture is None:
            return
        sub = self._sheet.subsurface(pygame.Rect(ox, oy, pw, ph))
        data = surface_rgba_bytes(sub)
        gl_y = self._tex_h - oy - ph
        self._texture.write(data, viewport=(ox, gl_y, pw, ph))

    def _flush_texture(self) -> None:
        if self._texture is None:
            data = surface_rgba_bytes(self._sheet)
            self._texture = self._ctx.texture((self._tex_w, self._tex_h), 4, data)
            self._texture.filter = (self._ctx.NEAREST, self._ctx.NEAREST)
            self._dirty_rects.clear()
            return
        for ox, oy, pw, ph in self._dirty_rects:
            self._upload_rect(ox, oy, pw, ph)
        self._dirty_rects.clear()

    def region(self, ch: str) -> GlyphRegion | None:
        if not ch or len(ch) != 1:
            return None
        reg = self._regions.get(ch)
        if reg is None:
            reg = self._bake(ch)
            self._flush_texture()
        return reg or self._regions.get("?")

    @property
    def texture(self):
        self._flush_texture()
        return self._texture

    def release(self) -> None:
        if self._texture is not None:
            self._texture.release()
            self._texture = None
