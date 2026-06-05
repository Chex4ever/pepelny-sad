"""Frame presentation: GPU map + batched UI glyphs."""
from __future__ import annotations

import pygame

from src.constants import COLOR_BG
from src.render.gpu.context import create_gpu_context
from src.render.gpu.iso_renderer import GpuIsoRenderer
from src.render.gpu.ui_renderer import GpuUiRenderer
from src.render.iso_projector import IsoProjector
from src.render.render_mode import set_gpu_fallback
from src.render.viewport import map_view_h, map_view_w


class GpuPresenter:
    def __init__(self, screen: pygame.Surface, _ascii_renderer_unused=None):
        self.available = False
        self._screen = screen
        self._gpu = create_gpu_context(screen.get_width(), screen.get_height())
        if self._gpu is None:
            set_gpu_fallback(True)
            return
        self._iso = GpuIsoRenderer(self._gpu)
        self._ui = GpuUiRenderer(self._gpu)
        self.available = True
        self.display_ms = 0.0

    def _clear_bg(self) -> None:
        bg = COLOR_BG[0] / 255.0, COLOR_BG[1] / 255.0, COLOR_BG[2] / 255.0
        self._gpu.ctx.clear(bg[0], bg[1], bg[2])

    def present_buffer(self, buffer, *, fade_alpha: int = 0) -> None:
        import time as _time

        t0 = _time.perf_counter()
        self._clear_bg()
        self._ui.draw(buffer, fade_alpha=fade_alpha)
        pygame.display.flip()
        self.display_ms = (_time.perf_counter() - t0) * 1000.0

    def render_overworld(self, game, *, fade_alpha: int = 0) -> None:
        import time as _time

        t0 = _time.perf_counter()
        ow = game.overworld
        assert ow is not None
        perf = game.perf
        wx0, wy0 = ow.camera.view_origin()
        vw, vh = map_view_w(), map_view_h()
        projector = IsoProjector()
        focus_wx, focus_wy = projector.view_focus(wx0, wy0, vw, vh)
        layer = game.world_state.layer
        queue = ow.map_renderer.last_iso_draw_queue

        with perf.measure("gpu_map"):
            self._iso.draw(queue, focus_wx=focus_wx, focus_wy=focus_wy)
        perf.set_counter("gpu_batch", self._iso.last_batch_quads)
        perf.set_counter("atlas_size", self._iso.atlas.texture_size)

        with perf.measure("gpu_ui"):
            self._ui.draw(game.buffer, fade_alpha=fade_alpha)
        perf.set_counter("ui_quads", self._ui.last_quad_count)
        perf._timers["gpu_ui_ms"] = self._ui.last_upload_ms

        pygame.display.flip()
        self.display_ms = (_time.perf_counter() - t0) * 1000.0
        perf._timers["display_ms"] = self.display_ms

    def release(self) -> None:
        if not self.available:
            return
        self._ui.release()
        self._iso.release()
        self._gpu.release()
