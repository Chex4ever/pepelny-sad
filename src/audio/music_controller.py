"""Scene/layer/weather music selection."""
from __future__ import annotations

from src.world.lighting import ambient_for_turn


class MusicController:
    PRIORITY = {
        "battle": 100,
        "dungeon": 80,
        "pepel": 60,
        "night": 40,
        "day": 30,
        "intro": 20,
        "title": 10,
        "ending": 10,
        "none": 0,
    }

    def __init__(self, audio):
        self.audio = audio
        self._scene = "title"
        self._layer = "surface"
        self._weather = False
        self._turn = 0
        self._active_key = "title"

    def on_scene(self, scene: str):
        self._scene = scene
        self._refresh()

    def on_layer(self, layer: str):
        self._layer = layer
        self._refresh()

    def on_weather(self, active: bool):
        self._weather = active
        self._refresh()

    def on_turn(self, turn_count: int):
        self._turn = turn_count
        if self._scene == "overworld" and self._layer == "surface":
            self._refresh()

    def _pick(self) -> tuple[str, str | None]:
        if self._scene == "battle":
            return "battle", "music_battle"
        if self._scene == "title":
            return "title", "music_title"
        if self._scene == "intro":
            return "intro", "music_intro"
        if self._scene == "ending":
            return "ending", "music_title"
        if self._layer == "dungeon":
            return "dungeon", "music_dungeon"
        if self._weather:
            return "pepel", "music_pepel"
        amb = ambient_for_turn(self._turn, "surface")
        if amb < 0.7:
            return "night", "music_surface_night"
        return "day", "music_surface_day"

    def _refresh(self):
        key, track = self._pick()
        if key == self._active_key and track == self.audio._current_music:
            return
        self._active_key = key
        self.audio.play_music(track)
