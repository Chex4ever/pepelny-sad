#!/usr/bin/env python3
"""Build PyInstaller onedir release for current platform."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_manifest import build_manifest
from tools.release_utils import detect_platform_id


def build(skip_audio: bool = False) -> Path:
    if not skip_audio:
        subprocess.run([sys.executable, str(ROOT / "tools" / "prepare_audio.py")], check=True, cwd=ROOT)

    subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(ROOT / "tools" / "pepelny_sad.spec"), "--noconfirm"],
        check=True,
        cwd=ROOT,
    )

    platform_id = detect_platform_id()
    built = ROOT / "dist" / "pepelny-sad"
    target = ROOT / "dist" / f"pepelny-sad-{platform_id}"
    if target.exists():
        shutil.rmtree(target)
    built.rename(target)

    manifest = build_manifest(target, platform_id)
    manifest_path = ROOT / "dist" / f"manifest-{platform_id}.json"
    import json

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    pepelny_meta = target / ".pepelny"
    pepelny_meta.mkdir(exist_ok=True)
    (pepelny_meta / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pepelny-sad release")
    parser.add_argument("--skip-audio", action="store_true")
    args = parser.parse_args()
    out = build(skip_audio=args.skip_audio)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
