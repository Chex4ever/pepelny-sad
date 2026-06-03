"""Shared runtime context passed to scenes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.audio.ambient_controller import AmbientController
    from src.audio.audio_manager import AudioManager
    from src.audio.music_controller import MusicController
    from src.progression.player_profile import PlayerProfile
    from src.ui.windows.window_manager import WindowManager
    from src.world.world_map import WorldMap
    from src.world.world_state import WorldState


@dataclass
class SceneContext:
    world_state: WorldState
    profile: PlayerProfile
    world_map: WorldMap
    audio: AudioManager
    ambient: AmbientController
    music: MusicController
    windows: WindowManager
    game: Any = field(repr=False)
    ending_data: dict | None = None
    title_seed: int = 0
    title_start_ms: int = 0
