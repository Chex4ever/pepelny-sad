#!/usr/bin/env python3
"""Inspect procedural trees: world layout, height, and iso views from four sides.

Run from repo root:
  python scripts/tree_viewer.py

Full-map GPU iso (same as game): use scripts/biome_viewer.py with T=trees.
The small iso panel here uses a local CPU projector for layout only.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import CELL_H, CELL_W, ISO_STEP_X, ISO_STEP_Y, init_paths
from src.data.art_loader import load_biomes
from src.render.iso_projector import IsoProjector
from src.render.tile_stencil import load_tile_stencil, stamp
from src.world.tree_generator import build_tree_solids, roll_tree_params

# View rotation: remap world (dx, dy) for display
_ROT_NAMES = ("Юг (+y)", "Восток (+x)", "Север (-y)", "Запад (-x)")


def _rotate_offset(dx: int, dy: int, view: int) -> tuple[int, int]:
    if view == 0:
        return dx, dy
    if view == 1:
        return dy, -dx
    if view == 2:
        return -dx, -dy
    return -dy, dx


def _draw_grid(
    surf: pygame.Surface,
    font: pygame.font.Font,
    ox: int,
    oy: int,
    cell: int,
    solids: list[tuple[int, int, object]],
    view: int,
    *,
    title: str,
) -> None:
    pygame.draw.rect(surf, (40, 45, 60), (ox - 2, oy - 18, cell * 11 + 4, cell * 11 + 22), 1)
    label = font.render(title, True, (200, 210, 220))
    surf.blit(label, (ox, oy - 16))
    by_type: dict[str, list[tuple[int, int]]] = {}
    for dx, dy, solid in solids:
        rx, ry = _rotate_offset(dx, dy, view)
        key = solid.stencil_id or "?"
        by_type.setdefault(key, []).append((rx, ry))
    all_cells: set[tuple[int, int]] = set()
    for cells in by_type.values():
        all_cells.update(cells)
    if not all_cells:
        return
    min_x = min(c[0] for c in all_cells)
    max_x = max(c[0] for c in all_cells)
    min_y = min(c[1] for c in all_cells)
    max_y = max(c[1] for c in all_cells)
    cx = (min_x + max_x) // 2
    cy = (min_y + max_y) // 2
    for dx, dy, solid in solids:
        rx, ry = _rotate_offset(dx, dy, view)
        px = ox + (rx - cx + 5) * cell
        py = oy + (ry - cy + 5) * cell
        if "trunk" in (solid.stencil_id or ""):
            color = (140, 100, 70)
            letter = "T"
        elif "canopy" in (solid.stencil_id or ""):
            color = (70, 130, 70)
            letter = "Y"
        else:
            color = (120, 120, 120)
            letter = "?"
        pygame.draw.rect(surf, (25, 30, 35), (px, py, cell - 1, cell - 1))
        txt = font.render(letter, True, color)
        surf.blit(txt, (px + 2, py + 1))
    pygame.draw.circle(surf, (255, 200, 80), (ox + 5 * cell, oy + 5 * cell), 4)
    leg = font.render("● якорь", True, (180, 180, 180))
    surf.blit(leg, (ox, oy + cell * 10 + 2))


def _draw_side_elevation(
    surf: pygame.Surface,
    font: pygame.font.Font,
    ox: int,
    oy: int,
    w: int,
    h: int,
    solids: list[tuple[int, int, object]],
    view: int,
) -> None:
    pygame.draw.rect(surf, (40, 45, 60), (ox, oy, w, h), 1)
    surf.blit(font.render("Бок (м высоты)", True, (200, 210, 220)), (ox + 4, oy + 2))
    scale_z = (h - 30) / 10.0
    scale_x = 24
    base_y = oy + h - 12
    for dx, dy, solid in solids:
        rx, _ry = _rotate_offset(dx, dy, view)
        x = ox + w // 2 + rx * scale_x
        z0 = solid.z_min
        z1 = solid.z_max
        y0 = int(base_y - z0 * scale_z)
        y1 = int(base_y - z1 * scale_z)
        if "trunk" in (solid.stencil_id or ""):
            col = (120, 90, 60)
        else:
            col = (60, 110, 60)
        pygame.draw.rect(surf, col, (x - 8, y1, 16, max(2, y0 - y1)))


def _draw_iso_preview(
    surf: pygame.Surface,
    font: pygame.font.Font,
    ox: int,
    oy: int,
    pw: int,
    ph: int,
    solids: list[tuple[int, int, object]],
    view: int,
    *,
    focus_wx: int = 0,
    focus_wy: int = 0,
) -> None:
    from src.render.screen_buffer import ScreenBuffer

    buf = ScreenBuffer(pw, ph)
    buf.clear(bg=(12, 14, 22))
    projector = IsoProjector(origin_x=pw // 2, origin_y=ph - 4)
    wx0, wy0 = 0, 0
    focus_wx, focus_wy = projector.view_focus(wx0, wy0, 1, 1)
    queue: list[tuple] = []
    queue.append((0, 0, 0, 0.0, "grass", (80, 110, 70), (20, 30, 20), 1.0, 0))
    for dx, dy, solid in solids:
        rwx, rwy = _rotate_offset(dx, dy, view)
        wx, wy = focus_wx + rwx, focus_wy + rwy
        sid = solid.stencil_id or "grass"
        z = solid.z_min
        queue.append((wx + wy, wx, wy, z, sid, (90, 120, 80), (20, 30, 20), 1.0, 0))
    queue.sort(key=lambda t: (t[0], t[3]))
    for _, wx, wy, z_m, sid, fg, bg, light, fog in queue:
        ax, ay = projector.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        if not buf.in_bounds(ax, ay):
            continue
        stencil = load_tile_stencil(sid)
        is_floor = z_m == 0.0
        stamp(
            buf,
            ax,
            ay,
            stencil,
            fg=fg,
            bg=bg,
            light=light,
            fog=fog,
            fill_iso_footprint=is_floor,
        )
    sub = pygame.Surface((pw * CELL_W, ph * CELL_H))
    sub.fill((12, 14, 22))
    glyph_font = pygame.font.SysFont("consolas", 14)
    for y in range(ph):
        for x in range(pw):
            ch = buf.chars[buf._idx(x, y)]
            if ch == " ":
                continue
            fg = buf.fg[buf._idx(x, y)]
            sub.blit(glyph_font.render(ch, True, fg), (x * CELL_W, y * CELL_H))
    scaled = pygame.transform.scale(sub, (pw * 6, ph * 8))
    surf.blit(scaled, (ox, oy))
    surf.blit(
        font.render(
            f"Изо схема (CPU) — в игре/GPU: biome_viewer + T  {ISO_STEP_X}x{ISO_STEP_Y}",
            True,
            (200, 210, 220),
        ),
        (ox, oy - 16),
    )


def main() -> int:
    init_paths(ROOT)
    pygame.init()
    pygame.display.set_caption("Просмотр деревьев — Пепельный Сад")
    win_w, win_h = 1100, 720
    screen = pygame.display.set_mode((win_w, win_h))
    font = pygame.font.SysFont("segoe ui", 14)
    small = pygame.font.SysFont("consolas", 13)

    biome = load_biomes().get("meadow", {})
    seed = 4242
    params = roll_tree_params(biome, seed, 0, 0)
    view = 0
    solids = build_tree_solids(params)

    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    view = (view - 1) % 4
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    view = (view + 1) % 4
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                    params = roll_tree_params(biome, seed, seed % 97, seed % 89)
                    solids = build_tree_solids(params)
                elif ev.key == pygame.K_UP:
                    params["height_m"] = min(10.0, params["height_m"] + 0.5)
                    solids = build_tree_solids(params)
                elif ev.key == pygame.K_DOWN:
                    params["height_m"] = max(3.0, params["height_m"] - 0.5)
                    solids = build_tree_solids(params)
                elif ev.key == pygame.K_t:
                    params["thick_trunk"] = not params.get("thick_trunk", False)
                    solids = build_tree_solids(params)
                elif ev.key == pygame.K_l:
                    params["lean"] = {-1: 0, 0: 1, 1: -1}.get(params.get("lean", 0), 0)
                    solids = build_tree_solids(params)

        screen.fill((18, 20, 28))
        lines = [
            "←/→ — поворот вида (4 стороны)   R — новое дерево   ↑/↓ — высота   T — толстый ствол   L — наклон",
            f"Вид: {_ROT_NAMES[view]}   seed={seed}",
            f"height={params['height_m']}m  radius={params['canopy_radius']}  lean={params['lean']}  "
            f"variant={params['variant']}  trunk={'thick' if params.get('thick_trunk') else 'slim'}",
            "В игре: старейшина @ (trigger), кузня & (forge) — у ворот святилища (чанк 0,0).",
        ]
        for i, line in enumerate(lines):
            screen.blit(small.render(line, True, (170, 180, 195)), (12, 8 + i * 16))

        _draw_grid(screen, small, 24, 100, 22, solids, view, title="Сверху (мировые клетки)")
        _draw_side_elevation(screen, small, 320, 100, 200, 200, solids, view)
        _draw_iso_preview(screen, small, 560, 90, 44, 28, solids, view)

        pygame.display.flip()
        pygame.time.wait(30)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
