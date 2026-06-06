"""Iso patch preview — same draw queue + render path as overworld (GPU by default)."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pygame

from src.constants import (
    CELL_H,
    CELL_W,
    COLOR_BG,
    ENTITY_DRAW_Z_M,
    ISO_ORIGIN_X,
    ISO_ORIGIN_Y,
    ISO_STEP_X,
    ISO_STEP_Y,
    SCREEN_H,
    SCREEN_W,
)
from src.render.iso_footprint import (
    footprint_bbox_ear_cells,
    internal_footprint_holes,
    iso_footprint_geom_pixel_rect,
    pixel_inside_iso_diamond,
    union_footprint,
)
from src.render.iso_projector import IsoProjector
from src.render.screen_buffer import ScreenBuffer
from src.render.tile_stencil import load_sprite, load_tile_stencil, stamp

if TYPE_CHECKING:
    from src.world.chunk import Chunk


def resolve_preview_mode(preferred: str | None = None) -> str:
    """Match game default: gpu when PEPELNY_RENDER=gpu and GL works, else iso."""
    raw = (preferred or os.environ.get("PEPELNY_RENDER", "gpu")).strip().lower()
    if raw in ("iso", "cpu"):
        return "iso"
    if raw == "gpu":
        # Explicit choice (OverworldPreview, biome_viewer loop) — do not probe GL here:
        # gl_available() used to create a standalone context and broke pygame's framebuffer.
        if preferred is not None:
            return "gpu"
        from src.render.gpu.context import gl_available

        return "gpu" if gl_available() else "iso"
    return "gpu" if _gl_available_safe() else "iso"


def _gl_available_safe() -> bool:
    try:
        from src.render.gpu.context import gl_available

        return gl_available()
    except Exception:
        return False


def preview_mode_label(mode: str) -> str:
    if mode == "gpu":
        return "GPU (как в игре, PEPELNY_RENDER=gpu)"
    return "CPU/iso (glyph + fill_iso_footprint)"


def build_surface_draw_queue(
    chunk: Chunk,
    wx0: int,
    wy0: int,
    w: int,
    h: int,
) -> list[tuple]:
    """Same queue layout and z rules as MapRenderer.build_iso_draw_queue (surface)."""
    queue: list[tuple] = []
    for dy in range(h):
        for dx in range(w):
            wx, wy = wx0 + dx, wy0 + dy
            col = chunk.to_column(dx, dy)
            queue.append(
                (
                    wx + wy,
                    wx,
                    wy,
                    col.floor_z,
                    col.floor_stencil_id,
                    col.fg,
                    col.bg,
                    1.0,
                    0,
                )
            )
            for solid in col.solids:
                if not solid.stencil_id:
                    continue
                sid = solid.stencil_id
                if "trunk" in sid:
                    z = col.floor_z + solid.z_min
                    sort_key = wx + wy + 120
                    sfg, sbg = (120, 85, 55), (35, 28, 20)
                elif "canopy" in sid:
                    z = col.floor_z + solid.z_min
                    sort_key = wx + wy + int((col.floor_z + solid.z_max) * 10)
                    sfg, sbg = col.fg, col.bg
                else:
                    z = col.floor_z + solid.z_min
                    sort_key = wx + wy + int(z * 10)
                    sfg, sbg = col.fg, col.bg
                queue.append((sort_key, wx, wy, z, sid, sfg, sbg, 1.0, 0))
    queue.sort(key=lambda t: (t[0], t[3]))
    return queue


SPRITE_PREVIEW_COLORS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "player": ((255, 220, 120), (8, 8, 18)),
    "companion": ((150, 200, 180), (8, 8, 18)),
}

_STENCIL_OBJECT_IDS: tuple[str, ...] = (
    "tree",
    "herb",
    "torch",
    "forge",
    "shard",
    "wall",
    "tree_trunk_slim",
    "tree_trunk_thick",
)


def list_sprite_ids() -> list[str]:
    from src.constants import DATA_DIR

    tiles = os.path.join(DATA_DIR, "art", "tiles")
    if not os.path.isdir(tiles):
        return ["player"]
    return sorted(
        name[:-4]
        for name in os.listdir(tiles)
        if name.endswith(".txt") and name[:-4] in SPRITE_PREVIEW_COLORS
    )


def list_object_preview_ids() -> list[str]:
    return [f"sprite:{sid}" for sid in list_sprite_ids()] + list(_STENCIL_OBJECT_IDS)


def iso_entity_sort_key(wx: int, wy: int, z_m: float) -> int:
    return wx + wy + int(z_m * 10)


def append_sprite_to_queue(
    queue: list[tuple],
    sprite_name: str,
    wx: int,
    wy: int,
    *,
    z_m: float | None = None,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
) -> None:
    sid = sprite_name if sprite_name.startswith("sprite:") else f"sprite:{sprite_name}"
    name = sid.split(":", 1)[1]
    pfg, pbg = SPRITE_PREVIEW_COLORS.get(name, ((255, 220, 120), (8, 8, 18)))
    pz = ENTITY_DRAW_Z_M if z_m is None else z_m
    queue.append(
        (
            iso_entity_sort_key(wx, wy, pz),
            wx,
            wy,
            pz,
            sid,
            pfg if fg is None else fg,
            pbg if bg is None else bg,
            1.0,
            0,
        )
    )
    queue.sort(key=lambda t: (t[0], t[3]))


def append_stencil_object_to_queue(
    queue: list[tuple],
    stencil_id: str,
    wx: int,
    wy: int,
    *,
    z_m: float = 0.0,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
) -> None:
    st = load_tile_stencil(stencil_id)
    queue.append(
        (
            iso_entity_sort_key(wx, wy, z_m),
            wx,
            wy,
            z_m,
            stencil_id,
            st.default_fg if fg is None else fg,
            st.default_bg if bg is None else bg,
            1.0,
            0,
        )
    )
    queue.sort(key=lambda t: (t[0], t[3]))


def build_object_preview_queue(
    object_id: str,
    *,
    wx: int,
    wy: int,
    floor_chunk: "Chunk | None" = None,
    wx0: int = 0,
    wy0: int = 0,
    w: int = 12,
    h: int = 12,
) -> list[tuple]:
    queue = (
        build_surface_draw_queue(floor_chunk, wx0, wy0, w, h)
        if floor_chunk is not None
        else []
    )
    if object_id.startswith("sprite:"):
        append_sprite_to_queue(queue, object_id, wx, wy)
    else:
        z = ENTITY_DRAW_Z_M if "trunk" in object_id else 0.0
        append_stencil_object_to_queue(queue, object_id, wx, wy, z_m=z)
    return queue


def drawn_floor_footprint_cells(
    queue: list[tuple],
    *,
    focus_wx: int,
    focus_wy: int,
    buf_w: int = SCREEN_W,
    buf_h: int = SCREEN_H,
    projector: IsoProjector | None = None,
) -> set[tuple[int, int]]:
    """Char cells whose center lies inside the GPU iso diamond union (paintable)."""
    p = projector or IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    bounds = floor_tile_geom_bounds(
        queue,
        focus_wx=focus_wx,
        focus_wy=focus_wy,
        buf_w=buf_w,
        buf_h=buf_h,
        projector=p,
    )
    anchors: list[tuple[int, int]] = []
    for _, wx, wy, z_m, sid, *_ in queue:
        if z_m != 0.0 or sid.startswith("sprite:"):
            continue
        ax, ay = p.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        if ax < -12 or ay < -16 or ax > buf_w + 12 or ay > buf_h + 16:
            continue
        anchors.append((ax, ay))
    covered = union_footprint(anchors)
    paintable: set[tuple[int, int]] = set()
    for cx, cy in covered:
        if not (0 <= cx < buf_w and 0 <= cy < buf_h):
            continue
        px = cx * CELL_W + CELL_W / 2
        py = cy * CELL_H + CELL_H / 2
        if pixel_inside_any_footprint(px, py, bounds):
            paintable.add((cx, cy))
    return paintable


def gpu_surface_bg_gaps(
    surf: pygame.Surface,
    covered: set[tuple[int, int]],
    *,
    bg: tuple[int, int, int] = COLOR_BG,
    tolerance: int = 2,
) -> list[tuple[int, int]]:
    """Screen cells in covered union that still show background RGB (GPU hole detector)."""
    gaps: list[tuple[int, int]] = []
    for cx, cy in covered:
        painted = False
        for ox, oy in (
            (CELL_W // 2, CELL_H // 2),
            (1, 1),
            (CELL_W - 2, 1),
            (1, CELL_H - 2),
            (CELL_W - 2, CELL_H - 2),
        ):
            px = cx * CELL_W + ox
            py = cy * CELL_H + oy
            if px >= surf.get_width() or py >= surf.get_height():
                continue
            r, g, b, *_ = surf.get_at((px, py))
            if not is_gpu_clear_pixel((r, g, b), bg=bg, tolerance=tolerance):
                painted = True
                break
        if not painted:
            gaps.append((cx, cy))
    return gaps


def drawn_floor_bbox_ear_cells(
    queue: list[tuple],
    *,
    focus_wx: int,
    focus_wy: int,
    buf_w: int = SCREEN_W,
    buf_h: int = SCREEN_H,
    projector: IsoProjector | None = None,
) -> set[tuple[int, int]]:
    """AABB corner ears from floor tiles visible on screen (bbox minus iso diamond)."""
    p = projector or IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    ears: set[tuple[int, int]] = set()
    for _, wx, wy, z_m, sid, *_ in queue:
        if z_m != 0.0 or sid.startswith("sprite:"):
            continue
        ax, ay = p.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        if ax < -12 or ay < -16 or ax > buf_w + 12 or ay > buf_h + 16:
            continue
        for cx, cy in footprint_bbox_ear_cells(ax, ay):
            if 0 <= cx < buf_w and 0 <= cy < buf_h:
                ears.add((cx, cy))
    return ears


def is_gpu_clear_pixel(
    rgb: tuple[int, int, int],
    *,
    bg: tuple[int, int, int] = COLOR_BG,
    tolerance: int = 2,
) -> bool:
    """Framebuffer clear color (symmetric — ignores dark glyph AA fringe)."""
    r, g, b = rgb
    return (
        abs(r - bg[0]) <= tolerance
        and abs(g - bg[1]) <= tolerance
        and abs(b - bg[2]) <= tolerance
    )


def is_gpu_background_pixel(
    rgb: tuple[int, int, int],
    *,
    bg: tuple[int, int, int] = COLOR_BG,
    tolerance: int = 2,
) -> bool:
    """Legacy loose bg check for char-cell gap scans."""
    r, g, b = rgb
    return (
        r <= bg[0] + tolerance
        and g <= bg[1] + tolerance
        and b <= bg[2] + tolerance
    )


def floor_tile_geom_bounds(
    queue: list[tuple],
    *,
    focus_wx: int,
    focus_wy: int,
    buf_w: int = SCREEN_W,
    buf_h: int = SCREEN_H,
    projector: IsoProjector | None = None,
) -> list[tuple[float, float, float, float]]:
    """GPU footprint AABB per visible floor tile (for pixel mask scans)."""
    p = projector or IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    bounds: list[tuple[float, float, float, float]] = []
    for _, wx, wy, z_m, sid, *_ in queue:
        if z_m != 0.0 or sid.startswith("sprite:"):
            continue
        ax, ay = p.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        if ax < -12 or ay < -16 or ax > buf_w + 12 or ay > buf_h + 16:
            continue
        bounds.append(iso_footprint_geom_pixel_rect(ax, ay))
    return bounds


def pixel_inside_any_footprint(
    px: float,
    py: float,
    tile_bounds: list[tuple[float, float, float, float]],
) -> bool:
    for x0, y0, x1, y1 in tile_bounds:
        if px < x0 or py < y0 or px >= x1 or py >= y1:
            continue
        if pixel_inside_iso_diamond(px, py, x0, y0):
            return True
    return False


def gpu_surface_footprint_pixel_artifacts(
    surf: pygame.Surface,
    tile_bounds: list[tuple[float, float, float, float]],
    *,
    bg: tuple[int, int, int] = COLOR_BG,
    tolerance: int = 2,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Union footprint mask: ears outside all diamonds; holes inside union showing clear color."""
    sw, sh = surf.get_width(), surf.get_height()
    if not tile_bounds:
        return [], []
    px_lo = max(0, min(int(b[0]) for b in tile_bounds))
    py_lo = max(0, min(int(b[1]) for b in tile_bounds))
    px_hi = min(sw, max(int(b[2]) for b in tile_bounds))
    py_hi = min(sh, max(int(b[3]) for b in tile_bounds))
    ears: list[tuple[int, int]] = []
    holes: list[tuple[int, int]] = []
    for py in range(py_lo, py_hi):
        for px in range(px_lo, px_hi):
            inside = pixel_inside_any_footprint(px + 0.5, py + 0.5, tile_bounds)
            r, g, b, *_ = surf.get_at((px, py))
            is_clear = is_gpu_clear_pixel((r, g, b), bg=bg, tolerance=tolerance)
            if inside and is_clear:
                holes.append((px, py))
            elif not inside and not is_clear:
                ears.append((px, py))
    return ears, holes


def build_footprint_mask_surface(
    tile_bounds: list[tuple[float, float, float, float]],
    *,
    width: int,
    height: int,
) -> pygame.Surface:
    """Debug mask: black outside footprint diamonds, white inside (pixel-exact)."""
    mask = pygame.Surface((width, height))
    mask.fill((0, 0, 0))
    for x0, y0, x1, y1 in tile_bounds:
        px_lo = max(0, int(x0))
        py_lo = max(0, int(y0))
        px_hi = min(width, int(x1))
        py_hi = min(height, int(y1))
        for py in range(py_lo, py_hi):
            for px in range(px_lo, px_hi):
                if pixel_inside_iso_diamond(px + 0.5, py + 0.5, x0, y0):
                    mask.set_at((px, py), (255, 255, 255))
    return mask


def gpu_surface_bbox_ear_leaks(
    surf: pygame.Surface,
    ears: set[tuple[int, int]],
    *,
    covered: set[tuple[int, int]] | None = None,
    bg: tuple[int, int, int] = COLOR_BG,
    tolerance: int = 2,
) -> list[tuple[int, int]]:
    """Ear cells outside the footprint union that show bbox corner bleed (not neighbor tiles)."""
    leaks: list[tuple[int, int]] = []
    for cx, cy in ears:
        if covered is not None and (cx, cy) in covered:
            continue
        px = cx * CELL_W + CELL_W // 2
        py = cy * CELL_H + CELL_H // 2
        if px >= surf.get_width() or py >= surf.get_height():
            continue
        r, g, b, *_ = surf.get_at((px, py))
        if not (
            r <= bg[0] + tolerance
            and g <= bg[1] + tolerance
            and b <= bg[2] + tolerance
        ):
            leaks.append((cx, cy))
    return leaks


def analyze_queue_footprint(
    queue: list[tuple],
    *,
    focus_wx: int,
    focus_wy: int,
    projector: IsoProjector | None = None,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]], set[tuple[int, int]]]:
    """Geometry holes in floor union; unstamped only meaningful for CPU path."""
    p = projector or IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    floor_anchors: list[tuple[int, int]] = []
    for _, wx, wy, z_m, sid, *_ in queue:
        if sid.startswith("sprite:") or z_m != 0.0:
            continue
        ax, ay = p.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        floor_anchors.append((ax, ay))
    covered = union_footprint(floor_anchors, step_x=ISO_STEP_X, step_y=ISO_STEP_Y)
    holes = internal_footprint_holes(covered)
    return holes, [], covered


def render_queue_cpu(
    queue: list[tuple],
    *,
    focus_wx: int,
    focus_wy: int,
    buf_w: int = SCREEN_W,
    buf_h: int = SCREEN_H,
) -> ScreenBuffer:
    buf = ScreenBuffer(buf_w, buf_h)
    buf.clear(bg=COLOR_BG)
    p = IsoProjector(origin_x=ISO_ORIGIN_X, origin_y=ISO_ORIGIN_Y)
    for _, wx, wy, z_m, sid, fg, bg, light, fog in queue:
        ax, ay = p.world_to_screen(wx, wy, z_m, focus_wx=focus_wx, focus_wy=focus_wy)
        if not buf.in_bounds(ax, ay):
            continue
        if sid.startswith("sprite:"):
            stencil = load_sprite(sid.split(":", 1)[1])
        else:
            stencil = load_tile_stencil(sid)
        is_floor = z_m == 0.0 and not sid.startswith("sprite:")
        stamp(
            buf,
            ax,
            ay,
            stencil,
            fg=fg,
            bg=bg,
            light=light,
            fog=fog,
            fill_iso_footprint=is_floor,
        )
    return buf


def buffer_to_surface(buf: ScreenBuffer, font: pygame.font.Font | None = None) -> pygame.Surface:
    font = font or pygame.font.SysFont("consolas", 14)
    surf = pygame.Surface((buf.width * CELL_W, buf.height * CELL_H))
    surf.fill(COLOR_BG)
    for y in range(buf.height):
        for x in range(buf.width):
            ch = buf.chars[buf._idx(x, y)]
            if ch == " ":
                continue
            fg = buf.fg[buf._idx(x, y)]
            surf.blit(font.render(ch, True, fg), (x * CELL_W, y * CELL_H))
    return surf


def read_gpu_framebuffer(ctx, pixel_w: int, pixel_h: int) -> pygame.Surface:
    data = bytes(ctx.screen.read(components=3))
    surf = pygame.image.frombuffer(data, (pixel_w, pixel_h), "RGB")
    return pygame.transform.flip(surf, False, True)


def present_gl_frame(screen: pygame.Surface) -> None:
    """Present moderngl draws on pygame OpenGL window."""
    pygame.display.flip()


def clear_preview_ui_buffer(buf: ScreenBuffer) -> None:
    """Match overworld GPU path: only explicit HUD glyphs get UI quads."""
    buf.clear(bg=COLOR_BG, bg_a=0, fg_a=0)


def draw_hud_lines(buf: ScreenBuffer, lines: list[str], *, start_row: int | None = None) -> None:
    if not lines:
        return
    start = start_row if start_row is not None else max(0, buf.height - len(lines))
    for i, line in enumerate(lines):
        y = start + i
        if y >= buf.height:
            break
        for x, ch in enumerate(line[: buf.width - 1]):
            if ch == " ":
                continue
            buf.set_fg_only(x, y, ch, fg=(200, 210, 220), fg_a=240)


class OverworldPreview:
    """Same pipeline as overworld: GpuIsoRenderer + GpuUiRenderer HUD (PEPELNY_RENDER=gpu)."""

    def __init__(self, mode: str | None = None):
        from src.render.render_mode import init_render_mode_from_env

        if mode:
            os.environ["PEPELNY_RENDER"] = mode
        init_render_mode_from_env()
        self.mode = resolve_preview_mode(mode)
        self.pixel_w = SCREEN_W * CELL_W
        self.pixel_h = SCREEN_H * CELL_H
        self.buffer = ScreenBuffer(SCREEN_W, SCREEN_H)
        self._presenter = None
        self._screen: pygame.Surface | None = None
        flags = 0
        if self.mode == "gpu":
            flags = pygame.OPENGL | pygame.DOUBLEBUF
        self._screen = pygame.display.set_mode((self.pixel_w, self.pixel_h), flags)
        if self.mode == "gpu":
            from src.render.gpu.presenter import GpuPresenter

            self._presenter = GpuPresenter(self._screen)
            if not self._presenter.available:
                self.mode = "iso"

    @property
    def mode_label(self) -> str:
        return preview_mode_label(self.mode)

    @property
    def available_gpu(self) -> bool:
        return self._presenter is not None and self._presenter.available

    def present(
        self,
        queue: list[tuple],
        *,
        focus_wx: int,
        focus_wy: int,
        hud_lines: list[str] | None = None,
    ) -> None:
        """Present map like overworld (GPU iso + optional HUD buffer)."""
        if self.mode == "gpu" and self.available_gpu:
            assert self._presenter is not None
            clear_preview_ui_buffer(self.buffer)
            if hud_lines:
                draw_hud_lines(self.buffer, hud_lines)
            from src.render.gpu.context import bind_screen_framebuffer

            bind_screen_framebuffer(self._presenter._gpu.ctx)
            self._presenter._iso.draw(queue, focus_wx=focus_wx, focus_wy=focus_wy)
            self._presenter._ui.draw(self.buffer)
            if self._screen is not None:
                present_gl_frame(self._screen)
            return
        self.buffer.clear(bg=COLOR_BG)
        render_queue_cpu(
            queue,
            focus_wx=focus_wx,
            focus_wy=focus_wy,
            buf_w=self.buffer.width,
            buf_h=self.buffer.height,
        )
        if hud_lines:
            draw_hud_lines(self.buffer, hud_lines)
        if self._screen is not None:
            surf = buffer_to_surface(self.buffer)
            self._screen.blit(surf, (0, 0))
            pygame.display.flip()

    def capture(
        self,
        queue: list[tuple],
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> pygame.Surface:
        if self.mode == "gpu" and self.available_gpu:
            assert self._presenter is not None
            self._presenter._iso.draw(queue, focus_wx=focus_wx, focus_wy=focus_wy)
            return read_gpu_framebuffer(
                self._presenter._gpu.ctx, self.pixel_w, self.pixel_h
            )
        buf = render_queue_cpu(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        return buffer_to_surface(buf)

    def release(self) -> None:
        if self._presenter is not None:
            self._presenter.release()


class IsoPreviewSession:
    """Window + GpuPresenter or CPU fallback; default render path = game GPU."""

    def __init__(
        self,
        pixel_w: int,
        pixel_h: int,
        mode: str | None = None,
        *,
        window: bool = True,
    ):
        self.pixel_w = pixel_w
        self.pixel_h = pixel_h
        self.mode = resolve_preview_mode(mode)
        self._window = window
        self._presenter = None
        self._screen: pygame.Surface | None = None
        self._font = pygame.font.SysFont("consolas", 14)

        if window:
            flags = 0
            if self.mode == "gpu":
                flags = pygame.OPENGL | pygame.DOUBLEBUF
            self._screen = pygame.display.set_mode((pixel_w, pixel_h), flags)
            if self.mode == "gpu":
                from src.render.gpu.presenter import GpuPresenter

                self._presenter = GpuPresenter(self._screen)
                if not self._presenter.available:
                    self.mode = "iso"

    @property
    def mode_label(self) -> str:
        return preview_mode_label(self.mode)

    def toggle_mode(self) -> str:
        self.mode = "iso" if self.mode == "gpu" else "gpu"
        if self._window:
            raise RuntimeError("toggle_mode requires restart viewer (OPENGL vs normal window)")
        return self.mode

    def capture_queue(
        self,
        queue: list[tuple],
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> pygame.Surface:
        if self.mode == "gpu" and self._presenter is not None and self._presenter.available:
            self._presenter._iso.draw(queue, focus_wx=focus_wx, focus_wy=focus_wy)
            if self._window:
                pygame.display.flip()
            return read_gpu_framebuffer(
                self._presenter._gpu.ctx, self.pixel_w, self.pixel_h
            )
        buf = render_queue_cpu(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        return buffer_to_surface(buf, self._font)

    def present_queue(
        self,
        queue: list[tuple],
        *,
        focus_wx: int,
        focus_wy: int,
    ) -> None:
        if self.mode == "gpu" and self._presenter is not None and self._presenter.available:
            self._presenter._iso.draw(queue, focus_wx=focus_wx, focus_wy=focus_wy)
            if self._window:
                pygame.display.flip()
            return
        buf = render_queue_cpu(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        if self._screen is not None:
            self._screen.blit(
                pygame.transform.scale(
                    buffer_to_surface(buf, self._font),
                    (self.pixel_w, self.pixel_h),
                ),
                (0, 0),
            )
            pygame.display.flip()

    def release(self) -> None:
        if self._presenter is not None:
            self._presenter.release()
