"""Guided onboarding steps for first-time overworld play."""
from __future__ import annotations

from src.i18n import t_list


class TutorialController:
    def __init__(self, game):
        self.game = game
        self._prev_pan = (0, 0)

    def _steps(self) -> list[str]:
        return t_list("ui.tutorial.steps")

    def active(self) -> bool:
        return self.game.world_state.tutorial_step >= 0

    def current_text(self) -> str:
        steps = self._steps()
        step = self.game.world_state.tutorial_step
        if step < 0 or step >= len(steps):
            return ""
        return steps[step]

    def advance(self) -> None:
        ws = self.game.world_state
        if ws.tutorial_step < 0:
            return
        ws.tutorial_step += 1
        if ws.tutorial_step >= len(self._steps()):
            ws.tutorial_step = -1

    def update_frame(self) -> None:
        if not self.active():
            return
        ow = self.game.overworld
        if not ow:
            return
        if self.game.world_state.tutorial_step == 1:
            pan = (ow.camera.pan_x, ow.camera.pan_y)
            if pan != self._prev_pan and (pan[0] != 0 or pan[1] != 0):
                self.advance()
            self._prev_pan = pan

    def notify_moved(self) -> None:
        if self.game.world_state.tutorial_step == 0:
            self.advance()

    def notify_examine_opened(self) -> None:
        if self.game.world_state.tutorial_step == 2:
            self.advance()

    def notify_sheet_opened(self) -> None:
        if self.game.world_state.tutorial_step == 3:
            self.advance()

    def notify_interacted(self) -> None:
        if self.game.world_state.tutorial_step == 4:
            self.advance()

    def notify_help_or_pause(self) -> None:
        if self.game.world_state.tutorial_step == 5:
            self.advance()
