"""Composite ScreenBuffer UI layer over the GPU map."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.render.gpu.quad import fullscreen_quad_bytes

if TYPE_CHECKING:
    from src.render.gpu.context import GpuContext
    from src.render.renderer import AsciiRenderer

_VERT = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
out vec2 v_uv;
uniform vec2 u_resolution;
void main() {
    vec2 ndc = (in_pos / u_resolution) * 2.0 - 1.0;
    ndc.y = -ndc.y;
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = in_uv;
}
"""

_FRAG = """
#version 330
in vec2 v_uv;
out vec4 f_color;
uniform sampler2D u_ui;
void main() {
    vec4 c = texture(u_ui, v_uv);
    if (c.a < 0.02) discard;
    f_color = c;
}
"""


class UiComposite:
    def __init__(self, gpu: GpuContext, width: int, height: int):
        self._gpu = gpu
        self._w = width
        self._h = height
        self._ui_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._prog = gpu.ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        w, h = float(width), float(height)
        self._vbo = gpu.ctx.buffer(fullscreen_quad_bytes(w, h))
        self._vao = gpu.ctx.vertex_array(
            self._prog, [(self._vbo, "2f 2f", "in_pos", "in_uv")]
        )
        self._texture = gpu.ctx.texture((width, height), 4)
        self._texture.filter = (gpu.ctx.NEAREST, gpu.ctx.NEAREST)
        self._prog["u_resolution"].value = (w, h)
        self.last_upload_ms = 0.0

    def draw_ui(
        self,
        buffer,
        ascii_renderer: AsciiRenderer,
        *,
        fade_alpha: int = 0,
    ) -> None:
        import time

        t0 = time.perf_counter()
        ctx = self._gpu.ctx
        self._ui_surface.fill((0, 0, 0, 0))
        ascii_renderer.draw_to_surface(self._ui_surface, buffer, global_alpha=255)
        if fade_alpha > 0:
            fade = pygame.Surface(self._ui_surface.get_size(), pygame.SRCALPHA)
            fade.fill((0, 0, 0, min(255, fade_alpha)))
            self._ui_surface.blit(fade, (0, 0))
        data = pygame.image.tostring(self._ui_surface, "RGBA")
        self._texture.write(data)
        self._texture.use(0)
        self._prog["u_ui"] = 0
        ctx.disable(ctx.CULL_FACE)
        ctx.enable(ctx.BLEND)
        self._vao.render(mode=ctx.TRIANGLES, vertices=6)
        self.last_upload_ms = (time.perf_counter() - t0) * 1000.0

    def release(self) -> None:
        self._texture.release()
        self._vbo.release()
        self._vao.release()
        self._prog.release()
