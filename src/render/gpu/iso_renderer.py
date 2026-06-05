"""Batched textured quads for isometric draw queue."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.constants import CELL_H, CELL_W, COLOR_BG, ISO_STEP_X, ISO_STEP_Y, SCREEN_H, SCREEN_W
from src.render.gpu.atlas import AtlasRegion, TileAtlas, preload_stencil_ids
from src.render.gpu.buffer_draw import draw_interleaved_triangles
from src.render.gpu.vertex_buffer import FloatBufferBuilder
from src.render.iso_footprint import iso_footprint_pixel_rect
from src.render.iso_projector import IsoProjector
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED
from src.render.tile_stencil import load_sprite, load_tile_stencil, SpriteStencil, TileStencil

if TYPE_CHECKING:
    from src.render.gpu.context import GpuContext

_VERT_SHADER = """
#version 330
in vec2 in_pos;
in vec4 in_color;
in float in_fog;
in vec4 in_bounds;
in vec4 in_uvbox;
out vec2 v_pos;
flat out vec4 v_bounds;
flat out vec4 v_uvbox;
out vec4 v_color;
out float v_fog;
uniform vec2 u_resolution;
void main() {
    vec2 ndc = (in_pos / u_resolution) * 2.0 - 1.0;
    ndc.y = -ndc.y;
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_pos = in_pos;
    v_bounds = in_bounds;
    v_uvbox = in_uvbox;
    v_color = in_color;
    v_fog = in_fog;
}
"""

_FRAG_SHADER = """
#version 330
in vec2 v_pos;
flat in vec4 v_bounds;
flat in vec4 v_uvbox;
in vec4 v_color;
in float v_fog;
out vec4 f_color;
uniform sampler2D u_atlas;

vec2 atlas_uv(vec2 pos, vec4 bounds, vec4 uvbox) {
    vec2 size = bounds.zw - bounds.xy;
    vec2 t = (pos - bounds.xy) / max(size, vec2(0.001));
    return vec2(mix(uvbox.x, uvbox.z, t.x), mix(uvbox.y, uvbox.w, t.y));
}

void main() {
    // Footprint fill uses solid biome tint (CPU stamps per cell); uvbox.x < 0 marks that path.
    if (v_uvbox.x < -0.5) {
        vec3 rgb = v_color.rgb;
        if (v_fog > 0.5) rgb *= 0.45;
        else if (v_fog > 0.1) rgb *= 0.75;
        f_color = vec4(rgb, v_color.a);
        return;
    }
    vec2 uv = atlas_uv(v_pos, v_bounds, v_uvbox);
    vec4 tex = texture(u_atlas, uv);
    vec3 rgb = tex.rgb * v_color.rgb;
    float a = tex.a * v_color.a;
    if (a < 0.02) discard;
    if (v_fog > 0.5) rgb *= 0.45;
    else if (v_fog > 0.1) rgb *= 0.75;
    f_color = vec4(rgb, a);
}
"""

_CULL_MARGIN_X = 12
_CULL_MARGIN_Y = 16


class GpuIsoRenderer:
    def __init__(self, gpu: GpuContext):
        self._gpu = gpu
        self._projector = IsoProjector()
        self._atlas = TileAtlas(gpu.ctx)
        self._atlas.preload(preload_stencil_ids())
        self._prog = gpu.ctx.program(
            vertex_shader=_VERT_SHADER, fragment_shader=_FRAG_SHADER
        )
        self._builder = FloatBufferBuilder()
        self._vbo_capacity = 0
        self._vbo = None
        self._vao = None
        self._ensure_vbo(2 * 1024 * 1024)
        self._pixel_w = SCREEN_W * CELL_W
        self._pixel_h = SCREEN_H * CELL_H
        self._prog["u_resolution"].value = (float(self._pixel_w), float(self._pixel_h))
        self.last_batch_quads = 0

    @property
    def atlas(self) -> TileAtlas:
        return self._atlas

    def _ensure_vbo(self, nbytes: int) -> None:
        need = max(nbytes, 256 * 1024)
        if self._vbo is not None and need <= self._vbo_capacity:
            return
        ctx = self._gpu.ctx
        if self._vao is not None:
            self._vao.release()
        if self._vbo is not None:
            self._vbo.release()
        self._vbo_capacity = max(need, self._vbo_capacity * 2, 2 * 1024 * 1024)
        self._vbo = ctx.buffer(reserve=self._vbo_capacity)
        self._vao = ctx.vertex_array(
            self._prog,
            [
                (
                    self._vbo,
                    "2f 4f 1f 4f 4f",
                    "in_pos",
                    "in_color",
                    "in_fog",
                    "in_bounds",
                    "in_uvbox",
                ),
            ],
        )

    def _draw_buffer(self, b: FloatBufferBuilder, ctx) -> None:
        """Upload and draw vertex data; chunk only on aligned triangle boundaries."""
        data = b.tobytes()
        stride = 15 * 4
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

    def _tint(self, rgb: tuple[int, int, int], light: float) -> tuple[float, float, float, float]:
        return tuple(max(0.0, min(1.0, c * light / 255.0)) for c in rgb) + (1.0,)

    def _fog_factor(self, fog: int) -> float:
        if fog == FOG_UNEXPLORED:
            return 1.0
        if fog == FOG_EXPLORED:
            return 0.5
        return 0.0

    def _stamp_stencil(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        stencil_id: str,
        *,
        fg: tuple[int, int, int],
        bg: tuple[int, int, int] | None = None,
        light: float,
        fog: int,
        expand_footprint: bool = False,
    ) -> None:
        if (
            anchor_cx < -_CULL_MARGIN_X
            or anchor_cy < -_CULL_MARGIN_Y
            or anchor_cx > SCREEN_W + _CULL_MARGIN_X
            or anchor_cy > SCREEN_H + _CULL_MARGIN_Y
        ):
            return
        fog_f = self._fog_factor(fog)
        if stencil_id.startswith("sprite:"):
            stencil: TileStencil | SpriteStencil = load_sprite(stencil_id.split(":", 1)[1])
        else:
            stencil = load_tile_stencil(stencil_id)
        fg_tint = self._tint(fg, light)
        bg_tint = self._tint(bg if bg is not None else stencil.default_bg, light)
        if expand_footprint:
            x0, y0, x1, y1 = iso_footprint_pixel_rect(anchor_cx, anchor_cy)
            b.append_quad_9(
                x0,
                y0,
                x1,
                y1,
                -1.0,
                -1.0,
                -1.0,
                -1.0,
                *bg_tint,
                fog_f,
            )
            self.last_batch_quads += 1
        reg = self._atlas.get_region(stencil_id)
        for g in stencil.glyphs:
            self._append_atlas_glyph_cell(
                b,
                anchor_cx + g.dx,
                anchor_cy + g.dy,
                reg,
                g.dx,
                g.dy,
                fg_tint,
                fog_f,
            )

    def _append_solid_cell(
        self,
        b: FloatBufferBuilder,
        cx: int,
        cy: int,
        tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        px0 = float(cx * CELL_W)
        py0 = float(cy * CELL_H)
        b.append_quad_9(
            px0,
            py0,
            px0 + CELL_W,
            py0 + CELL_H,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            *tint,
            fog_f,
        )
        self.last_batch_quads += 1

    def _glyph_uv_box(
        self, reg: AtlasRegion, glyph_dx: int, glyph_dy: int
    ) -> tuple[float, float, float, float]:
        lx = glyph_dx - reg.anchor_dx
        ly = glyph_dy - reg.anchor_dy
        cw = max(1, reg.pixel_w // CELL_W)
        ch = max(1, reg.pixel_h // CELL_H)
        du = (reg.u1 - reg.u0) / cw
        dv = (reg.v1 - reg.v0) / ch
        u0 = reg.u0 + lx * du
        u1 = u0 + du
        v1 = reg.v1 - ly * dv
        v0 = v1 - dv
        return u0, v0, u1, v1

    def _append_atlas_glyph_cell(
        self,
        b: FloatBufferBuilder,
        cx: int,
        cy: int,
        reg: AtlasRegion,
        glyph_dx: int,
        glyph_dy: int,
        tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        px0 = float(cx * CELL_W)
        py0 = float(cy * CELL_H)
        u0, v0, u1, v1 = self._glyph_uv_box(reg, glyph_dx, glyph_dy)
        b.append_quad_9(px0, py0, px0 + CELL_W, py0 + CELL_H, u0, v0, u1, v1, *tint, fog_f)
        self.last_batch_quads += 1

    def draw(
        self,
        draw_queue: list[tuple],
        *,
        focus_wx: int,
        focus_wy: int,
        entities: list[tuple] | None = None,
    ) -> None:
        from src.render.gpu.context import bind_screen_framebuffer

        ctx = self._gpu.ctx
        bind_screen_framebuffer(ctx)
        ctx.clear(COLOR_BG[0] / 255.0, COLOR_BG[1] / 255.0, COLOR_BG[2] / 255.0)
        b = self._builder
        b.clear()
        self.last_batch_quads = 0
        projector = self._projector

        for _, wx, wy, z_m, sid, fg, bg, light, fog in draw_queue:
            ax, ay = projector.world_to_screen(
                wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy
            )
            expand = z_m == 0.0 and not sid.startswith("sprite:")
            self._stamp_stencil(
                b,
                ax,
                ay,
                sid,
                fg=fg,
                bg=bg,
                light=light,
                fog=fog,
                expand_footprint=expand,
            )

        tex = self._atlas.ensure_texture()
        tex.use(0)
        self._prog["u_atlas"] = 0
        ctx.disable(ctx.CULL_FACE)
        ctx.enable(ctx.BLEND)
        if len(b) > 0:
            self._draw_buffer(b, ctx)

    def release(self) -> None:
        self._atlas.release()
        if self._vao is not None:
            self._vao.release()
            self._vao = None
        if self._vbo is not None:
            self._vbo.release()
            self._vbo = None
        self._prog.release()
