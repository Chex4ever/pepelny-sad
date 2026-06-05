#!/usr/bin/env python3
"""Preview iso meadow coverage using the same render path as the game (GPU by default).

Run: python scripts/meadow_preview.py
     python scripts/meadow_preview.py --render iso
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.constants import init_paths
from src.tools.iso_preview import OverworldPreview, analyze_queue_footprint, preview_mode_label

from scripts.biome_viewer import prepare_patch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", choices=("gpu", "iso"), default=None)
    parser.add_argument("--seed", type=int, default=4242)
    args = parser.parse_args()

    init_paths(ROOT)
    pygame.init()
    preview = OverworldPreview(args.render)
    pygame.display.set_caption(f"Поляна — {preview_mode_label(preview.mode)}")

    wx0, wy0, mw, mh = 0, 0, 14, 14
    seed = args.seed
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (
                ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE
            ):
                running = False

        _c, queue, stats, holes = prepare_patch(
            wx0, wy0, mw, mh, seed, "meadow", forced=True, trees=False, render_mode=preview.mode
        )
        focus_wx, focus_wy = wx0 + mw // 2, wy0 + mh // 2
        geom_holes, _, _ = analyze_queue_footprint(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        hud = [
            preview.mode_label,
            f"meadow {mw}x{mh} seed={seed}",
            f"geom holes {len(geom_holes)}  cpu unstamped {stats.unstamped_holes}",
            "Esc quit",
        ]
        preview.present(queue, focus_wx=focus_wx, focus_wy=focus_wy, hud_lines=hud)
        pygame.time.wait(50)

    preview.release()
    pygame.quit()
    return 0 if stats.internal_holes == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
