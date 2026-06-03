#!/usr/bin/env python3
"""Build zip update package for one patch step (e.g. 0.2.11 -> 0.2.12)."""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.updater.update_package import previous_patch_version, read_update_json_from_zip, update_package_filename
from src.version import read_version_file
from tools.release_utils import detect_platform_id, sha256_file


def scan_dist(dist_dir: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(dist_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(dist_dir).as_posix()
            files[rel] = sha256_file(path)
    return files


def load_prev_hashes(prev_zip: Path | None) -> dict[str, str]:
    if prev_zip is None or not prev_zip.is_file():
        return {}
    meta = read_update_json_from_zip(prev_zip)
    return {entry["path"]: entry["sha256"] for entry in meta.get("files", [])}


def build_update_package(
    dist_dir: Path,
    output_zip: Path,
    *,
    to_version: str | None = None,
    platform_id: str | None = None,
    prev_zip: Path | None = None,
) -> Path:
    platform_id = platform_id or detect_platform_id()
    to_version = to_version or read_version_file()
    from_version = previous_patch_version(to_version)

    current = scan_dist(dist_dir)
    prev_hashes = load_prev_hashes(prev_zip)
    if not prev_hashes:
        changed = [
            {"path": rel, "sha256": digest, "size": (dist_dir / rel).stat().st_size}
            for rel, digest in current.items()
        ]
    else:
        changed = []
        for rel, digest in current.items():
            if prev_hashes.get(rel) != digest:
                changed.append({"path": rel, "sha256": digest, "size": (dist_dir / rel).stat().st_size})

    meta = {
        "to_version": to_version,
        "platform": platform_id,
        "applies_from": [from_version],
        "files": changed,
    }

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("update.json", json.dumps(meta, indent=2) + "\n")
        for entry in changed:
            rel = entry["path"]
            zf.write(dist_dir / rel, rel)
    return output_zip


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pepelny-sad update zip")
    parser.add_argument("dist_dir", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--prev-zip", type=Path, default=None)
    parser.add_argument("--platform", default=None)
    parser.add_argument("--version", default=None)
    args = parser.parse_args()
    build_update_package(
        args.dist_dir,
        args.output,
        to_version=args.version,
        platform_id=args.platform,
        prev_zip=args.prev_zip,
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
