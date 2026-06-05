"""Title → fade out → loading → intro fade in."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.new_game_loader import iter_build_new_game
from src.i18n import t

if TYPE_CHECKING:
    from src.game import Game


class LoadingFlow:
    def __init__(self) -> None:
        self.active = False
        self.elapsed_ms = 0
        self.message = ""
        self.progress: float | None = None
        self._seed: int | None = None
        self._phase = "idle"
        self._build_gen = None

    def start_new_game(self, game: Game, seed: int) -> None:
        self.active = True
        self.elapsed_ms = 0
        self._seed = seed
        self._phase = "fade_out_title"
        self._build_gen = None
        self.message = t("loading.preparing")
        self.progress = 0.0
        game.transition.start_fade_out(lambda: self._on_title_fade_out_complete(game))

    def _on_title_fade_out_complete(self, game: Game) -> None:
        game.scene = "loading"
        self._phase = "building"
        self.message = t("loading.init")
        self.progress = 0.0
        self.elapsed_ms = 0
        self._build_gen = iter_build_new_game(game, self._seed)
        game.input.flush_pressed()

    def tick(self, game: Game, dt_ms: int) -> None:
        if not self.active or self._phase != "building":
            return
        self.elapsed_ms += dt_ms
        if self._build_gen is None:
            return
        try:
            self.message, self.progress = next(self._build_gen)
        except StopIteration:
            self._build_gen = None
            game.intro.reset()
            game.scene = "intro"
            game.input.flush_pressed()
            game.transition.start_fade_in()
            self.active = False
            self.message = ""
            self.progress = None

    def draw(self, game: Game) -> None:
        from src.ui.loading_screen import draw_loading

        draw_loading(
            game.buffer,
            self.message or t("loading.init"),
            elapsed_ms=self.elapsed_ms,
            progress=self.progress,
        )
