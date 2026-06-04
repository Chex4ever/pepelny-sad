#!/usr/bin/env python3
"""Generate simple isometric tile stencil prototypes from a char palette."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "data" / "art" / "tiles"


def diamond(fill: str, size: int = 3) -> list[str]:
    lines: list[str] = []
    for row in range(size):
        width = 2 + row * 2
        pad = " " * (size - row)
        core = (fill * width)[:width]
        lines.append(pad + core)
    for row in range(size - 2, -1, -1):
        width = 2 + row * 2
        pad = " " * (size - row)
        core = (fill * width)[:width]
        lines.append(pad + core)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Write tile stencil .txt files")
    parser.add_argument("name", help="stencil id (filename without .txt)")
    parser.add_argument("fill", help="character to fill diamond")
    parser.add_argument("--size", type=int, default=2)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{args.name}.txt"
    path.write_text("\n".join(diamond(args.fill, args.size)) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
