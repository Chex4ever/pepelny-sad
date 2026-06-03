#!/usr/bin/env python3
"""Build SHA256 manifest for a release directory."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.version import read_version_file
from tools.release_utils import detect_platform_id, github_download_url, path_to_asset_name, sha256_file


def build_manifest(
    dist_dir: Path,
    platform_id: str | None = None,
    *,
    repo: str = "Chex4ever/pepelny-sad",
    version: str | None = None,
) -> dict:
    platform_id = platform_id or detect_platform_id()
    version = version or read_version_file()
    tag = f"v{version}"
    files = []
    for path in sorted(dist_dir.rglob("*")):
        if not path.is_file():
            continue
        relpath = path.relative_to(dist_dir).as_posix()
        asset_name = path_to_asset_name(platform_id, relpath)
        files.append(
            {
                "path": relpath,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
                "asset": asset_name,
                "url": github_download_url(repo, tag, asset_name),
            }
        )
    return {
        "version": version,
        "platform": platform_id,
        "release_tag": tag,
        "repo": repo,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build release manifest.json")
    parser.add_argument("dist_dir", type=Path, help="PyInstaller onedir output directory")
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--platform", default=None)
    parser.add_argument("--repo", default="Chex4ever/pepelny-sad")
    args = parser.parse_args()
    manifest = build_manifest(args.dist_dir, args.platform, repo=args.repo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
