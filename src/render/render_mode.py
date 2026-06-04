"""Map render mode: isometric ASCII or classic 1-char-per-tile."""
from __future__ import annotations

import os

_MODE: str | None = None


def render_mode() -> str:
    global _MODE
    if _MODE is None:
        raw = os.environ.get("PEPELNY_RENDER", "iso").strip().lower()
        _MODE = raw if raw in ("iso", "classic") else "iso"
    return _MODE


def is_iso() -> bool:
    return render_mode() == "iso"


def is_classic() -> bool:
    return render_mode() == "classic"


def init_render_mode_from_env() -> None:
    """Re-read PEPELNY_RENDER (e.g. after main sets env before Game)."""
    global _MODE
    _MODE = None
    render_mode()
