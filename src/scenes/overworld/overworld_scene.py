"""Main overworld exploration scene (orchestrator)."""
from __future__ import annotations

import os

from src.constants import MAP_ORIGIN_Y, SCREEN_H
from src.render.viewport import map_view_h, map_view_w
from src.core.camera import Camera
from src.overworld.player import OverworldPlayer
from src.scenes.overworld.fov_controller import FovController
from src.scenes.overworld.input_router import OverworldInputRouter
from src.scenes.overworld.interaction import OverworldInteraction
from src.scenes.overworld.locomotion import LocomotionController
from src.scenes.overworld.map_renderer import MapRenderer
from src.story.dialogues import get_dialogue
from src.story.voices import voice_for_dialogue
from src.ui.hud.status_strip import StatusStrip
from src.ui.typewriter_dialogue import TypewriterDialogue
from src.scenes.overworld.world_sync import sync_for_draw, update_deferred
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.pepel_weather import PepelWeather


class OverworldScene:
    MAP_ORIGIN_Y = MAP_ORIGIN_Y

    def __init__(self, game):
        self.game = game
        self.player = OverworldPlayer()
        self.player.set_tile(20, 24)
        self.camera = Camera(map_view_w(), map_view_h())
        self.weather = PepelWeather(game.world_state.world_seed)
        self.dialogue = TypewriterDialogue()
        self.dialogue_open = False
        self.dialogue_id = ""
        self.pending_battle: str | None = None
        self.frame = 0
        self.visible: set[tuple[int, int]] = set()
        self.status = StatusStrip()
        self.fov = FovController(self)
        self.interaction = OverworldInteraction(self)
        self.map_renderer = MapRenderer(self)
        self.input_router = OverworldInputRouter(self)
        self.locomotion = LocomotionController(self)
        self._last_chunks_version = 0
        if game.world_state.layer == "dungeon":
            ensure_dungeon(game.world_state, game.world_map)
            self.player.set_tile(2, 2)

    @property
    def log(self):
        return self.game.windows.get("log")

    @property
    def sheet(self):
        return self.game.windows.get("sheet")

    @property
    def craft(self):
        return self.game.windows.get("craft")

    @property
    def examine(self):
        return self.game.windows.get("examine")

    def _is_explored(self, wx: int, wy: int) -> bool:
        return self.game.world_map.is_explored(wx, wy, self.game.world_state.layer)

    def prepare_draw(self, dt_ms: int = 16) -> None:
        """Camera + FOV for this frame (must run before draw uses ow.visible)."""
        perf = self.game.perf
        with perf.measure("ow_prepare"):
            self.game.world_state.world_time_s += dt_ms / 1000.0
            self.game.world_map.begin_frame()
            self.frame += 1
            if self.dialogue_open:
                self.dialogue.update(dt_ms, self.game.audio)
            self.camera.follow_smooth(self.player.x, self.player.y, dt_ms)
            cv = self.game.world_map.chunks_loaded_version()
            if cv != self._last_chunks_version:
                self._last_chunks_version = cv
                self.map_renderer.invalidate_queue_cache()
            sync_for_draw(self)

    def update_deferred(self, dt_ms: int = 16) -> None:
        update_deferred(self, dt_ms)

    def update(self, dt_ms: int = 16) -> None:
        """Full sync (tests/tools); in-game use prepare_draw + update_deferred."""
        self.prepare_draw(dt_ms)
        self.update_deferred(dt_ms)

    def handle_input(self, inp, dt_ms: int = 16) -> bool:
        if self.input_router.handle_input(inp, dt_ms):
            return True
        return self.locomotion.update(inp, dt_ms)

    def debug_lines(self, fps: float) -> list[str]:
        g = self.game
        wx0, wy0 = self.camera.view_origin()
        from src.constants import CHUNK_SIZE, VISIBLE_LOS_RADIUS_SURFACE
        from src.render.render_mode import render_mode, render_mode_label

        layer_id = g.world_state.layer
        layer_label = "поверхность" if layer_id == "surface" else "подземелье"
        ptx, pty = self.player.tile_pos()
        chunk_x = ptx // CHUNK_SIZE
        chunk_y = pty // CHUNK_SIZE
        weather = "шторм" if self.weather.active else "ясно"
        visible_n = len(self.visible)
        from src.render.render_mode import gpu_fallback_active

        fov_r = self.fov.fov_radius()
        perf_lines = g.perf.debug_lines(
            fps,
            render_mode=render_mode(),
            render_label=render_mode_label(),
            loaded_chunks=len(g.world_map.chunks),
            gpu_fallback=gpu_fallback_active(),
        )
        return perf_lines + [
            "--- мир ---",
            f"Рендер: {render_mode_label()}  (PEPELNY_RENDER={render_mode()})",
            f"Сцена: overworld",
            f"Layer: {layer_id} ({layer_label})",
            f"Time: {g.world_state.world_time_s:.1f}s  turns: {g.world_state.turn_count}",
            f"Seed: {g.world_state.world_seed}",
            f"Player: tile({ptx},{pty}) render({self.player.x:.2f},{self.player.y:.2f})",
            f"Camera: ({wx0}, {wy0}) pan ({self.camera.pan_x}, {self.camera.pan_y})",
            f"Chunk: ({chunk_x}, {chunk_y})  queue: {len(g.world_map._chunk_gen_queue)}",
            f"CPU: 1 main thread (GIL) / {os.cpu_count() or '?'} cores — PEPELNY_RUNTIME_CHUNK_WORKERS",
            f"FOV: los_r={fov_r} (base {VISIBLE_LOS_RADIUS_SURFACE})  visible={visible_n}  dirty={self.fov.is_dirty()}",
            f"Deferred: {g.perf._timers.get('deferred_ms', 0):.1f}ms  PEPELNY_SYNC_BUDGET_MS",
            f"Weather: {weather}",
            f"Companions: {len(g.world_state.companions)}",
            f"Boss cleared: {g.world_state.boss_cleared}",
        ]

    def _open_dialogue(self, did: str) -> None:
        self.interaction.open_dialogue(did)

    def draw(self, buf, inp=None):
        with self.game.perf.measure("ow_draw"):
            if inp:
                self.input_router.update_mouse_tooltip(inp)
            wx0, wy0 = self.camera.view_origin()
            with self.game.perf.measure("map_draw"):
                self.map_renderer.draw(buf, wx0, wy0)
            with self.game.perf.measure("status"):
                self.status.set_status(
                    self.game.world_state.layer,
                    self.game.world_state.turn_count,
                    pan_x=self.camera.pan_x,
                    pan_y=self.camera.pan_y,
                )
                self.status.draw(buf)
            if self.sheet:
                self.sheet.bind_profile(self.game.profile)
            if self.craft:
                self.craft.bind(self.game.profile, self.game.world_state)
            with self.game.perf.measure("windows"):
                self.game.windows.draw(buf)
            if self.dialogue_open and self.dialogue.active:
                self.dialogue.draw_box(buf, 10, SCREEN_H - 8, 70, 5)
            self.game.world_map.end_frame()

    @property
    def needs_battle(self) -> str | None:
        b = self.pending_battle
        self.pending_battle = None
        return b
