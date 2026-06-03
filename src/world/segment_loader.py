"""Load dungeon segments and stitch layout."""
from __future__ import annotations

import os
import random

from src import constants


def load_segment(name: str) -> tuple[list[str], dict]:
    base = os.path.join(constants.DATA_DIR, "segments", name)
    txt_path = base + ".txt"
    meta_path = base + ".meta"
    lines = []
    if os.path.isfile(txt_path):
        with open(txt_path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f.readlines()]
    meta = {"ports": {"N": 0, "E": 0, "S": 0, "W": 0}, "kind": "corridor"}
    if os.path.isfile(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            for line in mf:
                line = line.strip()
                if line.startswith("ports="):
                    parts = line.split("=", 1)[1].split(",")
                    meta["ports"] = {}
                    for part in parts:
                        part = part.strip()
                        if len(part) == 2:
                            meta["ports"][part[0]] = int(part[1])
                elif line.startswith("kind="):
                    meta["kind"] = line.split("=", 1)[1].strip()
    return lines, meta


SEGMENT_NAMES = [
    "corridor_01",
    "chamber_02",
    "trap_fog_03",
    "shrine_04",
    "loot_nook_05",
]


def stitch_dungeon(seed: int) -> list[dict]:
    rng = random.Random(seed ^ 0xDEAD)
    chain = []
    x, y = 0, 0
    for i, name in enumerate(SEGMENT_NAMES):
        lines, meta = load_segment(name)
        chain.append({"name": name, "x": x, "y": y, "lines": lines, "meta": meta})
        x += max(len(lines[0]) if lines else 16, 16) + 2
    return chain
