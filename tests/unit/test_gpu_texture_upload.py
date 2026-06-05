"""GPU atlas upload orientation."""
from __future__ import annotations

import pygame

from src.constants import CELL_H, CELL_W
from src.render.gpu.font_util import ui_font
from src.render.gpu.texture_upload import surface_rgba_bytes


def test_surface_rgba_bytes_has_glyph_alpha():
    pygame.init()
    font = ui_font()
    sheet = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA)
    sheet.fill((0, 0, 0, 0))
    sheet.blit(font.render("H", True, (255, 255, 255)), (0, 0))
    raw = surface_rgba_bytes(sheet)
    alphas = [raw[i + 3] for i in range(0, len(raw), 4)]
    assert max(alphas) > 200
