#!/usr/bin/env python3
"""Copy onedir files into GitHub Release asset filenames."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect_assets(manifest_path: Path, dist_dir: Path, output_dir: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for entry in manifest["files"]:
        src = dist_dir / entry["path"]
        dest = output_dir / entry["asset"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    collect_assets(args.manifest, args.dist_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
