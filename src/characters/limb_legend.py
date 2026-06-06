"""Limb color legend for character voxel viewer."""
from __future__ import annotations

import pygame

from src.characters.loader import load_palette
from src.characters.voxel_kinds import kind_glyph

# (voxel kind, Russian label)
CHARACTER_LIMB_LEGEND: tuple[tuple[str, str], ...] = (
    ("body_head", "голова"),
    ("body_torso", "торс"),
    ("body_arm_l", "рука L"),
    ("body_arm_r", "рука R"),
    ("body_leg_l", "нога L"),
    ("body_leg_r", "нога R"),
    ("hair", "волосы"),
    ("eye", "глаза"),
    ("armor_head", "шлем"),
    ("armor_chest", "броня"),
    ("weapon", "оружие"),
)


def kind_color(kind: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    pal = load_palette()
    entry = pal.get(kind)
    if entry:
        return tuple(entry["fg"]), tuple(entry["bg"])
    return (200, 200, 200), (30, 30, 30)


def draw_limb_legend(
    surf: pygame.Surface,
    *,
    x: int | None = None,
    y: int = 8,
    font: pygame.font.Font | None = None,
    items: tuple[tuple[str, str], ...] | None = None,
) -> None:
    """Draw color swatches + glyph + labels in top-right corner."""
    font = font or pygame.font.SysFont("consolas", 16)
    glyph_font = font
    legend = items or CHARACTER_LIMB_LEGEND
    swatch = max(14, font.get_height() - 2)
    line_h = font.get_height() + 4
    pad = max(8, font.get_height() // 2)
    max_label_w = max(font.size(f"{kind_glyph(k)} {label}")[0] for k, label in legend)
    box_w = pad * 2 + swatch + 4 + max_label_w
    box_h = pad * 2 + line_h * (len(legend) + 1)
    if x is None:
        x = surf.get_width() - box_w - 8
    bg = (16, 18, 28, 220)
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill(bg)
    pygame.draw.rect(panel, (70, 75, 95), panel.get_rect(), 1)
    panel.blit(font.render("части тела", True, (170, 175, 190)), (pad, pad - 1))
    ty = pad + line_h
    for kind, label in legend:
        fg, lb = kind_color(kind)
        glyph = kind_glyph(kind)
        rect = pygame.Rect(pad, ty + 1, swatch, swatch - 2)
        pygame.draw.rect(panel, lb, rect)
        pygame.draw.rect(panel, fg, rect.inflate(-2, -2))
        glyph_surf = glyph_font.render(glyph, True, fg)
        gx = pad + (swatch - glyph_surf.get_width()) // 2
        gy = ty + 1 + (swatch - 2 - glyph_surf.get_height()) // 2
        panel.blit(glyph_surf, (gx, gy))
        panel.blit(font.render(f"{glyph}  {label}", True, (200, 205, 220)), (pad + swatch + 4, ty))
        ty += line_h
    surf.blit(panel, (x, y))
