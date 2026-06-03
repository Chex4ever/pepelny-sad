"""Build dungeon from stitched segments."""
from __future__ import annotations

from src.world.segment_loader import stitch_dungeon


def ensure_dungeon(world_state, world_map):
    if world_state.dungeon_graph is not None:
        return world_state.dungeon_graph
    graph = stitch_dungeon(world_state.world_seed)
    ox, oy = 0, 0
    for seg in graph:
        sx, sy = seg["x"], seg["y"]
        for ly, line in enumerate(seg["lines"]):
            for lx, ch in enumerate(line):
                if ch == " ":
                    continue
                wx, wy = ox + sx + lx, oy + sy + ly
                fg = (100, 100, 120)
                bg = (18, 18, 26)
                if ch == "l":
                    fg = (255, 170, 70)
                elif ch == "!":
                    fg = (255, 90, 90)
                elif ch == "~":
                    fg = (120, 180, 200)
                world_map.set_dungeon_tile(wx, wy, ch, fg, bg)
    world_state.dungeon_graph = graph
    return graph
