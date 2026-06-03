"""Verify all art_id references have art files."""
from __future__ import annotations

import json
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data")
ART_ROOT = os.path.join(BASE, "art")


def _art_exists(art_id: str) -> bool:
    for sub in ("characters", "enemies", "items", "materials"):
        if os.path.isfile(os.path.join(ART_ROOT, sub, f"{art_id}.txt")):
            return True
    return False


def main():
    missing = []
    for fname in ("enemies.json", "items.json", "materials.json"):
        with open(os.path.join(BASE, fname), encoding="utf-8") as f:
            data = json.load(f)
        items = data.values() if isinstance(data, dict) else []
        for entry in items:
            aid = entry.get("art_id")
            if aid and not _art_exists(aid):
                missing.append(f"{fname}: {aid}")
    extras = ["elion", "elder", "whisper_companion", "sorrow_companion", "warden"]
    for aid in extras:
        if not _art_exists(aid):
            missing.append(f"character: {aid}")
    if missing:
        print("Missing art:")
        for m in missing:
            print(" ", m)
        sys.exit(1)
    print("Art audit OK")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.data.art_init import ensure_art_files
    from src.constants import init_paths

    init_paths(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ensure_art_files()
    main()
