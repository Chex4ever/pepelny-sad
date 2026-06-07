"""Batched textured quads for isometric draw queue.

GPU floor tiles mirror the CPU two-layer model (see docs/PERFORMANCE.md § GPU floor):

1. **Footprint (грунт)** — solid biome ``bg`` over all char cells in the iso diamond.
   CPU: ``fill_iso_footprint`` in ``stamp()``. GPU default: bbox undercoat + diamond clip.

2. **Stencil (декор)** — ASCII glyph cluster (e.g. grass.txt); atlas region is glyph bbox only,
   not a full tile bitmap. GPU: diamond splat or opaque ``splat:id`` bake.

``PEPELNY_GPU_FLOOR_MODE``: ``undercoat`` (default) | ``opaque_splat`` | ``glyphs``.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from src.constants import (
    CELL_H,
    CELL_W,
    COLOR_BG,
    ISO_STEP_X,
    ISO_STEP_Y,
    SCREEN_H,
    SCREEN_W,
)
from src.render.gpu.atlas import AtlasRegion, TileAtlas, preload_stencil_ids
from src.render.gpu.buffer_draw import draw_interleaved_from_builder
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
uniform int u_texless;

uniform float u_diamond_half_w;
uniform float u_diamond_mid_h;
uniform float u_fp_bbox_w;
uniform float u_fp_bbox_h;

vec2 atlas_uv(vec2 pos, vec4 bounds, vec4 uvbox) {
    vec2 size = bounds.zw - bounds.xy;
    vec2 t = (pos - bounds.xy) / max(size, vec2(0.001));
    return vec2(mix(uvbox.x, uvbox.z, t.x), mix(uvbox.y, uvbox.w, t.y));
}

bool inside_iso_diamond(vec2 pos, vec4 bounds, float slack) {
    float px = bounds.x + u_diamond_half_w;
    float py = bounds.y + u_diamond_mid_h;
    vec2 d = pos - vec2(px, py);
    float ax = abs(d.x);
    if (d.y >= 0.0) {
        return ax / u_diamond_half_w + d.y / (2.0 * u_diamond_mid_h) <= slack;
    }
    return ax / u_diamond_half_w + (-d.y) / u_diamond_mid_h <= slack;
}

bool is_footprint_aabb(vec4 bounds) {
    vec2 sz = bounds.zw - bounds.xy;
    return abs(sz.x - u_fp_bbox_w) < 1.0 && abs(sz.y - u_fp_bbox_h) < 1.0;
}

float fog_strength(float fog) {
    if (fog >= 2.0) fog -= 2.0;
    return fog;
}

void main() {
    if (is_footprint_aabb(v_bounds) && (v_fog >= 2.0 || v_uvbox.x < -0.5)) {
        if (!inside_iso_diamond(v_pos, v_bounds, 1.001)) discard;
    }
    if (is_footprint_aabb(v_bounds) && u_texless == 0 && v_uvbox.x >= -0.5 && v_fog < 2.0
        && !inside_iso_diamond(v_pos, v_bounds, 1.001)) {
        discard;
    }
    float fog = fog_strength(v_fog);
    // Footprint fill uses solid biome tint (CPU stamps per cell); uvbox.x < 0 marks that path.
    if (v_uvbox.x < -0.5) {
        vec3 rgb = v_color.rgb;
        if (fog > 0.5) rgb *= 0.45;
        else if (fog > 0.1) rgb *= 0.75;
        f_color = vec4(rgb, v_color.a);
        return;
    }
    if (u_texless != 0) {
        vec3 rgb = v_color.rgb;
        if (fog > 0.5) rgb *= 0.45;
        else if (fog > 0.1) rgb *= 0.75;
        f_color = vec4(rgb, v_color.a);
        return;
    }
    vec2 uv = atlas_uv(v_pos, v_bounds, v_uvbox);
    vec4 tex = texture(u_atlas, uv);
    vec3 rgb = tex.rgb * v_color.rgb;
    float a = tex.a * v_color.a;
    if (a < 0.02) discard;
    if (fog > 0.5) rgb *= 0.45;
    else if (fog > 0.1) rgb *= 0.75;
    f_color = vec4(rgb, a);
}
"""

_CULL_MARGIN_X = 12
_CULL_MARGIN_Y = 16
# v_fog >= this encodes bbox footprint quads that clip to the iso diamond (no AABB ears).
_FOG_DIAMOND_CLIP = 2.0


def _diamond_geom(anchor_cx: int, anchor_cy: int) -> tuple[float, ...]:
    """Fast iso diamond corners + footprint AABB (no per-cell footprint scan)."""
    px = float(anchor_cx * CELL_W)
    py = float(anchor_cy * CELL_H)
    x0 = float((anchor_cx - ISO_STEP_X) * CELL_W)
    y0 = float((anchor_cy - ISO_STEP_Y) * CELL_H)
    x1 = float((anchor_cx + ISO_STEP_X + 1) * CELL_W)
    y1 = float((anchor_cy + 2 * ISO_STEP_Y + 1) * CELL_H)
    right = float((anchor_cx + ISO_STEP_X) * CELL_W)
    left = float((anchor_cx - ISO_STEP_X) * CELL_W)
    mid_y = float((anchor_cy + ISO_STEP_Y) * CELL_H)
    top_y = float((anchor_cy + 2 * ISO_STEP_Y) * CELL_H)
    return px, py, right, left, mid_y, top_y, x0, y0, x1, y1


def gpu_splat_enabled() -> bool:
    """Atlas splat: 1 quad per floor tile (PEPELNY_GPU_SPLAT, default on)."""
    raw = os.environ.get("PEPELNY_GPU_SPLAT", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def gpu_floor_mode() -> str:
    """Floor draw path: undercoat | opaque_splat | glyphs (PEPELNY_GPU_FLOOR_MODE)."""
    raw = os.environ.get("PEPELNY_GPU_FLOOR_MODE", "undercoat").strip().lower()
    if raw in ("opaque", "opaque_splat", "splat"):
        return "opaque_splat"
    if raw in ("glyphs", "legacy", "per_glyph"):
        return "glyphs"
    return "undercoat"


def gpu_bench_texless() -> bool:
    """PEPELNY_BENCH: skip atlas sampling in fragment (stable perf gate timing)."""
    raw = os.environ.get("PEPELNY_BENCH", "").strip().lower()
    return raw in ("1", "true", "yes")


def gpu_bench_active() -> bool:
    return gpu_bench_texless()


def _atlas_uv_corners(reg: AtlasRegion) -> tuple[float, float, float, float]:
    """Screen top → atlas top (reg.v1); matches ui_renderer and GL upload flip."""
    return reg.u0, reg.v1, reg.u1, reg.v0


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
        self._prog["u_diamond_half_w"].value = float(ISO_STEP_X * CELL_W)
        self._prog["u_diamond_mid_h"].value = float(ISO_STEP_Y * CELL_H)
        self._prog["u_fp_bbox_w"].value = float((2 * ISO_STEP_X + 1) * CELL_W)
        self._prog["u_fp_bbox_h"].value = float((3 * ISO_STEP_Y + 1) * CELL_H)
        self.last_batch_quads = 0
        self._cached_draw_key: object = None
        self._cached_vertex_count = 0
        self._cached_batch_quads = 0

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
        """Upload and draw vertex data (zero-copy array buffer when possible)."""
        stride = 15 * 4
        verts = len(b) // 15
        if verts < 3:
            return
        draw_interleaved_from_builder(
            ctx,
            self._vao,
            self._vbo,
            self._vbo_capacity,
            self._ensure_vbo,
            b.byte_buffer(),
            stride,
            verts,
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
        if gpu_splat_enabled() and gpu_floor_mode() != "glyphs" and not stencil_id.startswith(
            "sprite:"
        ):
            if expand_footprint:
                self._append_floor_tile(
                    b,
                    anchor_cx,
                    anchor_cy,
                    stencil_id,
                    fg=fg,
                    bg=bg if bg is not None else fg,
                    light=light,
                    fog_f=fog_f,
                )
            else:
                fg_tint = self._tint(fg, light)
                if gpu_bench_texless():
                    self._append_atlas_splat_texless(b, anchor_cx, anchor_cy, fg_tint, fog_f)
                else:
                    reg = self._atlas.get_region(stencil_id)
                    self._append_atlas_splat(b, anchor_cx, anchor_cy, reg, fg_tint, fog_f)
            return
        if stencil_id.startswith("sprite:"):
            stencil: TileStencil | SpriteStencil = load_sprite(stencil_id.split(":", 1)[1])
        else:
            stencil = load_tile_stencil(stencil_id)
        fg_tint = self._tint(fg, light)
        bg_tint = self._tint(bg if bg is not None else stencil.default_bg, light)
        if expand_footprint:
            self._append_footprint_undercoat(b, anchor_cx, anchor_cy, bg_tint, fog_f)
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
        # Screen top (t.y=0) must sample atlas top (high V after GL row-flip upload).
        v_top = reg.v1 - ly * dv
        v_bot = v_top - dv
        return u0, v_top, u1, v_bot

    def _append_footprint_bbox_quad(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        u0: float,
        v0: float,
        u1: float,
        v1: float,
        tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        """Footprint AABB quad clipped to iso diamond in the fragment shader."""
        *_, x0, y0, x1, y1 = _diamond_geom(anchor_cx, anchor_cy)
        r, g, bl, a = tint
        b.append_quad_9(
            x0,
            y0,
            x1,
            y1,
            u0,
            v0,
            u1,
            v1,
            r,
            g,
            bl,
            a,
            _FOG_DIAMOND_CLIP + fog_f,
        )
        self.last_batch_quads += 1

    def _append_footprint_undercoat(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        bg_tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        """Solid bbox under splat — full cell coverage, diamond clip removes corner ears."""
        self._append_footprint_bbox_quad(
            b, anchor_cx, anchor_cy, -1.0, -1.0, -1.0, -1.0, bg_tint, fog_f
        )

    def _append_atlas_splat_texless(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        geom = _diamond_geom(anchor_cx, anchor_cy)
        r, g, bl, a = tint
        b.append_diamond_splat_15(*geom, 0.0, 0.0, 1.0, 1.0, r, g, bl, a, fog_f)
        self.last_batch_quads += 1

    def _append_atlas_splat(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        reg: AtlasRegion,
        tint: tuple[float, float, float, float],
        fog_f: float,
    ) -> None:
        geom = _diamond_geom(anchor_cx, anchor_cy)
        r, g, bl, a = tint
        ru0, rv0, ru1, rv1 = _atlas_uv_corners(reg)
        b.append_diamond_splat_15(*geom, ru0, rv0, ru1, rv1, r, g, bl, a, fog_f)
        self.last_batch_quads += 1

    def _append_floor_tile(
        self,
        b: FloatBufferBuilder,
        anchor_cx: int,
        anchor_cy: int,
        stencil_id: str,
        *,
        fg: tuple[int, int, int],
        bg: tuple[int, int, int],
        light: float,
        fog_f: float,
    ) -> None:
        """Floor tile — mode from PEPELNY_GPU_FLOOR_MODE."""
        mode = gpu_floor_mode()
        fg_tint = self._tint(fg, light)
        if mode == "opaque_splat":
            bg_tint = self._tint(bg, light)
            self._append_footprint_undercoat(b, anchor_cx, anchor_cy, bg_tint, fog_f)
            if gpu_bench_texless():
                self._append_atlas_splat_texless(b, anchor_cx, anchor_cy, fg_tint, fog_f)
            else:
                reg = self._atlas.get_region(f"splat:{stencil_id}")
                self._append_atlas_splat(b, anchor_cx, anchor_cy, reg, fg_tint, fog_f)
            return
        bg_tint = self._tint(bg, light)
        self._append_footprint_undercoat(b, anchor_cx, anchor_cy, bg_tint, fog_f)
        if gpu_bench_texless():
            self._append_atlas_splat_texless(b, anchor_cx, anchor_cy, fg_tint, fog_f)
        else:
            reg = self._atlas.get_region(stencil_id)
            self._append_atlas_splat(b, anchor_cx, anchor_cy, reg, fg_tint, fog_f)

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
        queue_cache_key: object | None = None,
    ) -> None:
        from src.render.gpu.context import bind_screen_framebuffer

        ctx = self._gpu.ctx
        bind_screen_framebuffer(ctx, width=self._gpu.width, height=self._gpu.height)
        ctx.clear(COLOR_BG[0] / 255.0, COLOR_BG[1] / 255.0, COLOR_BG[2] / 255.0)
        b = self._builder
        draw_key: object = (
            queue_cache_key
            if gpu_bench_texless() and queue_cache_key is not None
            else (id(draw_queue), focus_wx, focus_wy)
        )
        if draw_key == self._cached_draw_key and self._cached_vertex_count >= 3:
            self.last_batch_quads = self._cached_batch_quads
            texless = 1 if gpu_bench_texless() else 0
            self._prog["u_texless"].value = texless
            if not texless:
                tex = self._atlas.ensure_texture()
                tex.use(0)
                self._prog["u_atlas"] = 0
            ctx.disable(ctx.CULL_FACE)
            ctx.enable(ctx.BLEND)
            draw_interleaved_from_builder(
                ctx,
                self._vao,
                self._vbo,
                self._vbo_capacity,
                self._ensure_vbo,
                b.byte_buffer(),
                15 * 4,
                self._cached_vertex_count,
            )
            return

        b.clear()
        self.last_batch_quads = 0
        projector = self._projector
        use_splat = gpu_splat_enabled() and gpu_floor_mode() != "glyphs"
        texless = gpu_bench_texless()
        cull_r = SCREEN_W + _CULL_MARGIN_X
        cull_b = SCREEN_H + _CULL_MARGIN_Y

        for _, wx, wy, z_m, sid, fg, _bg, light, fog in draw_queue:
            ax, ay = projector.world_to_screen(
                wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy
            )
            if ax < -_CULL_MARGIN_X or ay < -_CULL_MARGIN_Y or ax > cull_r or ay > cull_b:
                continue
            if use_splat and not sid.startswith("sprite:"):
                fog_f = 1.0 if fog == FOG_UNEXPLORED else (0.5 if fog == FOG_EXPLORED else 0.0)
                if z_m == 0.0:
                    self._append_floor_tile(
                        b,
                        ax,
                        ay,
                        sid,
                        fg=fg,
                        bg=_bg,
                        light=light,
                        fog_f=fog_f,
                    )
                    continue
                fg_tint = self._tint(fg, light)
                if texless:
                    self._append_atlas_splat_texless(b, ax, ay, fg_tint, fog_f)
                else:
                    reg = self._atlas.get_region(sid)
                    self._append_atlas_splat(b, ax, ay, reg, fg_tint, fog_f)
                continue
            expand = z_m == 0.0 and not sid.startswith("sprite:")
            self._stamp_stencil(
                b,
                ax,
                ay,
                sid,
                fg=fg,
                bg=_bg,
                light=light,
                fog=fog,
                expand_footprint=expand,
            )

        texless = 1 if gpu_bench_texless() else 0
        self._prog["u_texless"].value = texless
        if not texless:
            tex = self._atlas.ensure_texture()
            tex.use(0)
            self._prog["u_atlas"] = 0
        ctx.disable(ctx.CULL_FACE)
        ctx.enable(ctx.BLEND)
        if len(b) > 0:
            self._draw_buffer(b, ctx)
            self._cached_draw_key = draw_key
            self._cached_vertex_count = len(b) // 15
            self._cached_batch_quads = self.last_batch_quads

    def release(self) -> None:
        self._atlas.release()
        if self._vao is not None:
            self._vao.release()
            self._vao = None
        if self._vbo is not None:
            self._vbo.release()
            self._vbo = None
        self._prog.release()
