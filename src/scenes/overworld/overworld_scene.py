"""Main overworld exploration scene (orchestrator)."""
from __future__ import annotations

from src.constants import MAP_ORIGIN_Y, MAP_VIEW_H, MAP_VIEW_W, SCREEN_H
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
        self.camera = Camera(MAP_VIEW_W, MAP_VIEW_H)
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
        self.frame += 1
        if self.dialogue_open:
            self.dialogue.update(dt_ms, self.game.audio)
        self.camera.center_on(self.player.x, self.player.y)
        wx0, wy0 = self.camera.view_origin()
        self.visible = self.fov.update(wx0, wy0)

    def handle_input(self, inp):
        return self.input_router.handle_input(inp)

    def _open_dialogue(self, did: str) -> None:
        self.interaction.open_dialogue(did)

    def draw(self, buf, inp=None):
        if inp:
            self.input_router.update_mouse_tooltip(inp)
        wx0, wy0 = self.camera.view_origin()
        self.map_renderer.draw(buf, wx0, wy0)
        self.status.set_status(self.game.world_state.layer, self.game.world_state.turn_count)
        self.status.draw(buf)
        if self.sheet:
            self.sheet.bind_profile(self.game.profile)
        if self.craft:
            self.craft.bind(self.game.profile, self.game.world_state)
        self.game.windows.draw(buf)
        if self.dialogue_open and self.dialogue.active:
            self.dialogue.draw_box(buf, 10, SCREEN_H - 8, 70, 5, title="ДИАЛОГ")

    @property
    def needs_battle(self) -> str | None:
        b = self.pending_battle
        self.pending_battle = None
        return b
