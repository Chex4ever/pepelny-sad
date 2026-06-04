"""Main overworld exploration scene (orchestrator)."""
from __future__ import annotations

from src.constants import MAP_ORIGIN_Y, SCREEN_H
from src.render.viewport import map_view_h, map_view_w
from src.core.camera import Camera
from src.overworld.player import OverworldPlayer
from src.scenes.overworld.fov_controller import FovController
from src.scenes.overworld.input_router import OverworldInputRouter
from src.scenes.overworld.interaction import OverworldInteraction
from src.scenes.overworld.map_renderer import MapRenderer
from src.story.dialogues import get_dialogue
from src.story.voices import voice_for_dialogue
from src.ui.hud.status_strip import StatusStrip
from src.ui.typewriter_dialogue import TypewriterDialogue
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.pepel_weather import PepelWeather


class OverworldScene:
    MAP_ORIGIN_Y = MAP_ORIGIN_Y

    def __init__(self, game):
        self.game = game
        self.player = OverworldPlayer(x=20, y=24)
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
        if game.world_state.layer == "dungeon":
            ensure_dungeon(game.world_state, game.world_map)
            self.player.x, self.player.y = 2, 2

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

    def update(self, dt_ms: int = 16):
        perf = self.game.perf
        with perf.measure("ow_update"):
            self.game.world_map.begin_frame()
            self.frame += 1
            if self.dialogue_open:
                self.dialogue.update(dt_ms, self.game.audio)
            self.camera.center_on(self.player.x, self.player.y)
            self.game.world_map._ensure_radius(self.player.x, self.player.y)
            wx0, wy0 = self.camera.view_origin()
            with perf.measure("fov"):
                self.visible = self.fov.update(wx0, wy0)

    def handle_input(self, inp):
        return self.input_router.handle_input(inp)

    def debug_lines(self, fps: float) -> list[str]:
        g = self.game
        wx0, wy0 = self.camera.view_origin()
        from src.constants import CHUNK_SIZE
        from src.render.render_mode import render_mode

        layer_id = g.world_state.layer
        layer_label = "поверхность" if layer_id == "surface" else "подземелье"
        chunk_x = self.player.x // CHUNK_SIZE
        chunk_y = self.player.y // CHUNK_SIZE
        weather = "шторм" if self.weather.active else "ясно"
        visible_n = len(self.visible)
        perf_lines = g.perf.debug_lines(
            fps,
            render_mode=render_mode(),
            loaded_chunks=len(g.world_map.chunks),
        )
        return perf_lines + [
            "---",
            f"Сцена: overworld",
            f"Layer: {layer_id} ({layer_label})",
            f"Turn: {g.world_state.turn_count}",
            f"Seed: {g.world_state.world_seed}",
            f"Player: ({self.player.x}, {self.player.y})",
            f"Camera: ({wx0}, {wy0}) pan ({self.camera.pan_x}, {self.camera.pan_y})",
            f"Chunk: ({chunk_x}, {chunk_y})",
            f"Visible tiles: {visible_n}",
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
            self.game.windows.draw(buf)
            if self.dialogue_open and self.dialogue.active:
                self.dialogue.draw_box(buf, 10, SCREEN_H - 8, 70, 5)
            self.game.world_map.end_frame()

    @property
    def needs_battle(self) -> str | None:
        b = self.pending_battle
        self.pending_battle = None
        return b
