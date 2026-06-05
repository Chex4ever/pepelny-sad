"""GPU UI: ScreenBuffer → batched glyph quads (no per-frame font.render)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.constants import CELL_H, CELL_W, SCREEN_H, SCREEN_W
from src.render.gpu.glyph_atlas import GlyphAtlas
from src.render.gpu.buffer_draw import draw_interleaved_triangles
from src.render.gpu.vertex_buffer import FloatBufferBuilder
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED

if TYPE_CHECKING:
    from src.render.gpu.context import GpuContext

_VERT = """
#version 330
in vec2 in_pos;
in vec2 in_uv;
in vec3 in_fg;
in vec3 in_bg;
in float in_bga;
in float in_light;
in float in_fog;
in float in_fg_a;
in vec4 in_bounds;
in vec4 in_uvbox;
out vec2 v_pos;
flat out vec4 v_bounds;
flat out vec4 v_uvbox;
out vec3 v_fg;
out vec3 v_bg;
out float v_bga;
out float v_light;
out float v_fog;
out float v_fg_a;
uniform vec2 u_resolution;
void main() {
    vec2 ndc = (in_pos / u_resolution) * 2.0 - 1.0;
    ndc.y = -ndc.y;
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_pos = in_pos;
    v_bounds = in_bounds;
    v_uvbox = in_uvbox;
    v_fg = in_fg;
    v_bg = in_bg;
    v_bga = in_bga;
    v_light = in_light;
    v_fog = in_fog;
    v_fg_a = in_fg_a;
}
"""

_FRAG = """
#version 330
in vec2 v_pos;
flat in vec4 v_bounds;
flat in vec4 v_uvbox;
in vec3 v_fg;
in vec3 v_bg;
in float v_bga;
in float v_light;
in float v_fog;
in float v_fg_a;
out vec4 f_color;
uniform sampler2D u_glyphs;
vec2 glyph_uv(vec2 pos, vec4 bounds, vec4 uvbox) {
    vec2 size = bounds.zw - bounds.xy;
    vec2 t = (pos - bounds.xy) / max(size, vec2(0.001));
    return vec2(mix(uvbox.x, uvbox.z, t.x), mix(uvbox.y, uvbox.w, t.y));
}

void main() {
    vec2 uv = glyph_uv(v_pos, v_bounds, v_uvbox);
    vec4 g = texture(u_glyphs, uv);
    vec3 bg = v_bg * v_light;
    vec3 fg = v_fg * v_light;
    float ga = g.a * v_fg_a;
    vec3 rgb = mix(bg, fg, ga);
    float alpha = max(ga, v_bga);
    if (ga < 0.02 && v_bga > 0.01) {
        f_color = vec4(v_bg * v_light, v_bga);
        return;
    }
    if (v_fog > 0.5) rgb *= 0.45;
    else if (v_fog > 0.1) rgb *= 0.75;
    if (alpha < 0.02) discard;
    f_color = vec4(rgb, alpha);
}
"""

_FLOATS_PER_VERTEX = 20


class GpuUiRenderer:
    def __init__(self, gpu: GpuContext):
        self._gpu = gpu
        self._glyphs = GlyphAtlas(gpu.ctx)
        self._prog = gpu.ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        self._builder = FloatBufferBuilder()
        self._vbo_capacity = 0
        self._vbo = None
        self._vao = None
        self._ensure_vbo(512 * 1024)
        w = float(SCREEN_W * CELL_W)
        h = float(SCREEN_H * CELL_H)
        self._prog["u_resolution"].value = (w, h)
        self.last_quad_count = 0
        self.last_upload_ms = 0.0

    def _ensure_vbo(self, nbytes: int) -> None:
        if self._vbo is not None and nbytes <= self._vbo_capacity:
            return
        ctx = self._gpu.ctx
        if self._vao is not None:
            self._vao.release()
        if self._vbo is not None:
            self._vbo.release()
        self._vbo_capacity = max(nbytes, 512 * 1024)
        self._vbo = ctx.buffer(reserve=self._vbo_capacity)
        self._vao = ctx.vertex_array(
            self._prog,
            [
                (
                    self._vbo,
                    "2f 3f 3f 1f 1f 1f 1f 4f 4f",
                    "in_pos",
                    "in_fg",
                    "in_bg",
                    "in_bga",
                    "in_light",
                    "in_fog",
                    "in_fg_a",
                    "in_bounds",
                    "in_uvbox",
                ),
            ],
        )

    def _tint(self, rgb: tuple[int, int, int], light: float) -> tuple[float, float, float]:
        return tuple(max(0.0, min(1.0, c * light / 255.0)) for c in rgb)

    def _fog(self, fog: int) -> float:
        if fog == FOG_UNEXPLORED:
            return 1.0
        if fog == FOG_EXPLORED:
            return 0.5
        return 0.0

    def draw(self, buffer, *, fade_alpha: int = 0) -> None:
        import time

        from src.render.gpu.context import bind_screen_framebuffer

        t0 = time.perf_counter()
        ctx = self._gpu.ctx
        bind_screen_framebuffer(ctx)
        b = self._builder
        b.clear()
        w, h = buffer.width, buffer.height
        cw, ch = CELL_W, CELL_H
        glyphs = self._glyphs
        append = b.append_quad_12
        quads = 0

        for y in range(h):
            py0 = float(y * ch)
            py1 = py0 + ch
            row = y * w
            for x in range(w):
                i = row + x
                ch_char = buffer.chars[i]
                fog = buffer.fog[i]
                bg_a = buffer.bg_a[i]
                if ch_char == " " and fog == 0 and bg_a < 8:
                    continue
                px0 = float(x * cw)
                px1 = px0 + cw
                light = buffer.light[i]
                fr, fg_c, fb = self._tint(buffer.fg[i], light)
                br, bg_c, bb = self._tint(buffer.bg[i], light)
                ba = min(1.0, bg_a / 255.0)
                fa = min(1.0, buffer.fg_a[i] / 255.0)
                fog_f = self._fog(fog)
                if ch_char != " ":
                    reg = glyphs.region(ch_char)
                    if reg is None:
                        reg = glyphs.region("?")
                    if reg is not None:
                        append(
                            px0,
                            py0,
                            px1,
                            py1,
                            reg.u0,
                            reg.v1,
                            reg.u1,
                            reg.v0,
                            fr,
                            fg_c,
                            fb,
                            br,
                            bg_c,
                            bb,
                            ba,
                            light,
                            fog_f,
                            fa,
                        )
                        quads += 1
                        continue
                if bg_a > 0:
                    append(
                        px0,
                        py0,
                        px1,
                        py1,
                        0.0,
                        0.0,
                        0.01,
                        0.01,
                        br,
                        bg_c,
                        bb,
                        br,
                        bg_c,
                        bb,
                        ba,
                        light,
                        fog_f,
                        1.0,
                    )
                    quads += 1

        self.last_quad_count = quads
        tex = self._glyphs.texture
        tex.use(0)
        self._prog["u_glyphs"] = 0
        ctx.disable(ctx.CULL_FACE)
        ctx.enable(ctx.BLEND)
        ctx.blend_func = ctx.SRC_ALPHA, ctx.ONE_MINUS_SRC_ALPHA
        if len(b) > 0:
            data = b.tobytes()
            stride = _FLOATS_PER_VERTEX * 4
            if len(data) > self._vbo_capacity:
                self._ensure_vbo(len(data))
            draw_interleaved_triangles(
                ctx,
                self._vao,
                self._vbo,
                self._vbo_capacity,
                self._ensure_vbo,
                data,
                stride,
            )

        self.last_upload_ms = (time.perf_counter() - t0) * 1000.0

    def release(self) -> None:
        self._glyphs.release()
        if self._vao is not None:
            self._vao.release()
        if self._vbo is not None:
            self._vbo.release()
        self._prog.release()
