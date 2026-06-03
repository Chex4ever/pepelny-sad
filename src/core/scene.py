"""Scene protocol for game states."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.scene_context import SceneContext
    from src.input import InputState
    from src.render.screen_buffer import ScreenBuffer


class Scene(ABC):
    @abstractmethod
    def update(self, dt_ms: int, ctx: SceneContext) -> None:
        ...

    @abstractmethod
    def handle_input(self, inp: InputState, ctx: SceneContext) -> bool:
        """Return True if scene requests a world action (e.g. layer change)."""
        ...

    @abstractmethod
    def draw(self, buf: ScreenBuffer, ctx: SceneContext, inp: InputState | None = None) -> None:
        ...
