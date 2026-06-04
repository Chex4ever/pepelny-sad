#!/usr/bin/env python3
"""Preview parametric trees at several heights."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.render.procedural_stencil import procedural_tree_canopy, procedural_tree_trunk
from src.world.tree_generator import build_tree_solids, roll_tree_params


def _stencil_lines(stencil) -> list[str]:
    if not stencil.glyphs:
        return ["?"]
    min_dx = min(g.dx for g in stencil.glyphs)
    max_dx = max(g.dx for g in stencil.glyphs)
    min_dy = min(g.dy for g in stencil.glyphs)
    max_dy = max(g.dy for g in stencil.glyphs)
    rows: dict[int, dict[int, str]] = {}
    for g in stencil.glyphs:
        rows.setdefault(g.dy, {})[g.dx] = g.ch
    lines = []
    for dy in range(min_dy, max_dy + 1):
        line = []
        for dx in range(min_dx, max_dx + 1):
            line.append(rows.get(dy, {}).get(dx, " "))
        lines.append("".join(line).rstrip())
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", default="tree_preview.txt")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    biome = {"tree_height_m": [3, 10]}
    parts: list[str] = []
    for h in (3, 5, 7, 10):
        params = roll_tree_params(biome, args.seed, h * 11, h * 13)
        params["height_m"] = float(h)
        parts.append(f"=== height {h}m variant {params['variant']} radius {params['canopy_radius']} ===")
        trunk = procedural_tree_trunk(params.get("thick_trunk", False))
        parts.extend(_stencil_lines(trunk))
        parts.append("-- canopy --")
        canopy = procedural_tree_canopy(params["variant"], int(h), params["canopy_radius"])
        parts.extend(_stencil_lines(canopy))
        parts.append("-- solids --")
        for dx, dy, solid in build_tree_solids(params):
            parts.append(
                f"  ({dx},{dy}) z={solid.z_min:.1f}-{solid.z_max:.1f} "
                f"move={solid.blocks_movement} {solid.stencil_id}"
            )
        parts.append("")
    out_path = os.path.join(ROOT, args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
