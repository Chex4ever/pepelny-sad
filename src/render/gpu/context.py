"""ModernGL context lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GpuContext:
    ctx: Any
    width: int
    height: int
    available: bool = True
    _programs: dict[str, Any] = field(default_factory=dict)

    def release(self) -> None:
        if self.ctx is not None:
            try:
                self.ctx.release()
            except Exception:
                pass
        self.ctx = None
        self.available = False


def bind_screen_framebuffer(
    ctx, *, width: int | None = None, height: int | None = None
) -> None:
    """Ensure draws go to the pygame swapchain back buffer (not an orphan FBO)."""
    screen = getattr(ctx, "screen", None)
    if screen is not None:
        screen.use()
        ctx.viewport = (0, 0, screen.width, screen.height)
    elif width is not None and height is not None:
        ctx.viewport = (0, 0, width, height)


def configure_bench_gl_attributes() -> None:
    """Disable vsync for benchmark timing (call before pygame.display.set_mode)."""
    import os

    if os.environ.get("PEPELNY_BENCH", "").strip().lower() not in ("1", "true", "yes"):
        return
    try:
        import pygame

        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)
    except Exception:
        pass


def create_gpu_context(width: int, height: int) -> GpuContext | None:
    try:
        import moderngl  # noqa: F401
    except ImportError:
        return None
    try:
        import os

        import moderngl

        ctx = moderngl.create_context()
        bind_screen_framebuffer(ctx, width=width, height=height)
        ctx.disable(ctx.DEPTH_TEST)
        ctx.disable(ctx.CULL_FACE)
        return GpuContext(ctx=ctx, width=width, height=height)
    except Exception:
        return None


_GL_AVAILABLE_CACHE: bool | None = None


def _pygame_gl_surface_active() -> bool:
    try:
        import pygame

        if not pygame.get_init():
            return False
        surf = pygame.display.get_surface()
        if surf is None:
            return False
        return bool(surf.get_flags() & pygame.OPENGL)
    except Exception:
        return False


def gl_available(*, force_probe: bool = False) -> bool:
    """Probe OpenGL once; never spawn standalone context over active pygame GL."""
    global _GL_AVAILABLE_CACHE
    if not force_probe and _GL_AVAILABLE_CACHE is not None:
        return _GL_AVAILABLE_CACHE
    if not force_probe and _pygame_gl_surface_active():
        _GL_AVAILABLE_CACHE = True
        return True
    try:
        import moderngl

        moderngl.create_context(standalone=True).release()
        _GL_AVAILABLE_CACHE = True
    except Exception:
        _GL_AVAILABLE_CACHE = False
    return _GL_AVAILABLE_CACHE
