"""Map render mode: isometric ASCII, classic, or GPU-accelerated iso."""
from __future__ import annotations

import os

_MODE: str | None = None
_GPU_FALLBACK: bool = False


def render_mode() -> str:
    global _MODE
    if _MODE is None:
        raw = os.environ.get("PEPELNY_RENDER", "iso").strip().lower()
        _MODE = raw if raw in ("iso", "classic", "gpu") else "iso"
    return _MODE


def is_iso() -> bool:
    return render_mode() in ("iso", "gpu")


def is_classic() -> bool:
    return render_mode() == "classic"


def is_gpu() -> bool:
    return render_mode() == "gpu" and not _GPU_FALLBACK


def gpu_fallback_active() -> bool:
    return _GPU_FALLBACK


def set_gpu_fallback(active: bool = True) -> None:
    global _GPU_FALLBACK
    _GPU_FALLBACK = active


def init_render_mode_from_env() -> None:
    """Re-read PEPELNY_RENDER (e.g. after main sets env before Game)."""
    global _MODE, _GPU_FALLBACK
    _MODE = None
    _GPU_FALLBACK = False
    render_mode()


def render_mode_label() -> str:
    """Human-readable active render path for debug HUD."""
    mode = render_mode()
    if mode == "gpu":
        if is_gpu():
            return "GPU (OpenGL + atlas)"
        return "GPU запрошен → CPU iso (нет GL)"
    if mode == "iso":
        return "ISO (CPU, stencil/glyph)"
    if mode == "classic":
        return "CLASSIC (1 символ на тайл)"
    return f"неизвестно ({mode})"
