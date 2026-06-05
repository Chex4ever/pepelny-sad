"""Fullscreen quad helpers (pygame top-left → OpenGL)."""
from __future__ import annotations

import struct


def fullscreen_quad_bytes(width: float, height: float) -> bytes:
    """Two CCW triangles covering (0,0)..(w,h) in pygame pixel coords.

    UV (0,0) = top-left of uploaded texture (pygame row 0 at GL tex origin).
    Vertex shader must flip Y when converting to NDC.
    """
    w, h = float(width), float(height)
    return struct.pack(
        "24f",
        0.0,
        0.0,
        0.0,
        0.0,
        w,
        0.0,
        1.0,
        0.0,
        w,
        h,
        1.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        w,
        h,
        1.0,
        1.0,
        0.0,
        h,
        0.0,
        1.0,
    )
