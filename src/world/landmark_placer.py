"""Load and stamp landmarks."""
from __future__ import annotations

import os

from src import constants
from src.constants import CHUNK_SIZE
from src.world.chunk import Chunk


LANDMARK_POSITIONS = {
    "sanctuary_gate": (0, 0),
    "broken_lantern_road": (2, -1),
    "ivy_crossing": (4, 0),
}


def _load_landmark(name: str) -> list[str]:
    path = os.path.join(constants.DATA_DIR, "landmarks", f"{name}.txt")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f.readlines()]


def stamp_landmark(chunk: Chunk, landmark_id: str, ox: int = 0, oy: int = 0):
    lines = _load_landmark(landmark_id)
    if not lines:
        return
    for ly, line in enumerate(lines):
        for lx, ch in enumerate(line):
            if ch == " ":
                continue
            tx, ty = ox + lx, oy + ly
            if chunk.in_bounds(tx, ty):
                fg = (180, 190, 200)
                bg = (25, 28, 35)
                if ch in "l":
                    fg = (255, 180, 80)
                elif ch == "!":
                    fg = (255, 100, 100)
                elif ch == "&":
                    fg = (220, 180, 100)
                elif ch == ">":
                    fg = (120, 200, 255)
                elif ch == "@":
                    fg = (255, 230, 160)
                chunk.set(tx, ty, ch, fg=fg, bg=bg)


def apply_landmarks(chunks: dict[tuple[int, int], Chunk], seed: int):
    for lid, (cx, cy) in LANDMARK_POSITIONS.items():
        key = (cx, cy)
        if key not in chunks:
            continue
        chunk = chunks[key]
        for ly in range(CHUNK_SIZE):
            for lx in range(CHUNK_SIZE):
                if chunk.get(lx, ly) in "T,o,+":
                    chunk.set(lx, ly, ".", fg=(100, 130, 90), bg=(30, 45, 30))
        stamp_landmark(chunk, lid, ox=4, oy=8)
