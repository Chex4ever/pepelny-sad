#!/usr/bin/env python3
"""Create GitHub Release and upload assets with rate-limit friendly batching."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PRIMARY_SUFFIXES = (
    "manifest-win-x64.json",
    "manifest-linux-x64.json",
)
PRIMARY_GLOBS = (
    "-win-x64-setup.exe",
    "-linux-x64.tar.gz",
)


def is_primary_asset(name: str) -> bool:
    if name in PRIMARY_SUFFIXES:
        return True
    return any(name.endswith(suffix) for suffix in PRIMARY_GLOBS)


def run_gh(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"gh failed: {args}").strip())
    return proc


def delete_existing_release(tag: str) -> None:
    run_gh(["release", "delete", tag, "--yes"], check=False)


def create_release(tag: str, title: str, primary_files: list[Path]) -> None:
    args = ["release", "create", tag, "--title", title, "--generate-notes"]
    if primary_files:
        args.extend(str(path) for path in primary_files)
    run_gh(args)


def upload_batch(tag: str, files: list[Path], *, clobber: bool) -> None:
    args = ["release", "upload", tag]
    if clobber:
        args.append("--clobber")
    args.extend(str(path) for path in files)
    for attempt in range(6):
        proc = run_gh(args, check=False)
        if proc.returncode == 0:
            return
        err = (proc.stderr or proc.stdout or "").lower()
        if "rate limit" in err or "secondary rate" in err:
            wait = min(60, 5 * (attempt + 1))
            print(f"Rate limited, retry in {wait}s ({len(files)} files)...", flush=True)
            time.sleep(wait)
            continue
        raise RuntimeError((proc.stderr or proc.stdout or "upload failed").strip())
    raise RuntimeError(f"Upload failed after retries: {[f.name for f in files]}")


def publish_assets(asset_dir: Path, tag: str, *, batch_size: int, delay_s: float) -> None:
    files = sorted(p for p in asset_dir.iterdir() if p.is_file())
    primary = [p for p in files if is_primary_asset(p.name)]
    incremental = [p for p in files if not is_primary_asset(p.name)]

    delete_existing_release(tag)
    create_release(tag, tag, primary)

    print(f"Uploading {len(incremental)} incremental assets in batches of {batch_size}...", flush=True)
    for i in range(0, len(incremental), batch_size):
        batch = incremental[i : i + batch_size]
        upload_batch(tag, batch, clobber=True)
        if i + batch_size < len(incremental):
            time.sleep(delay_s)

    print(json.dumps({"tag": tag, "primary": len(primary), "incremental": len(incremental)}))


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish GitHub release assets")
    parser.add_argument("asset_dir", type=Path)
    parser.add_argument("tag", help="Release tag, e.g. v0.2.9")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--delay", type=float, default=2.5)
    args = parser.parse_args()
    publish_assets(args.asset_dir, args.tag, batch_size=args.batch_size, delay_s=args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
