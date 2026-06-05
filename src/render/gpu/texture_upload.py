"""Upload pygame surfaces to OpenGL textures (pygame top-left → GL bottom-left)."""
from __future__ import annotations

import pygame


def surface_rgba_bytes(surface: pygame.Surface) -> bytes:
    """Row-flip so ScreenBuffer / pygame Y matches OpenGL texture V."""
    flipped = pygame.transform.flip(surface, False, True)
    return pygame.image.tostring(flipped, "RGBA")
