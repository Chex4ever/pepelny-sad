"""Tests for F1/Esc modals and LOG visibility."""
from __future__ import annotations

import pygame

from src.core.scene_manager import SceneManager
from tests.conftest import FakeInput, drain_transition


def test_f1_opens_help_same_frame(game):
    g = game
    g.scene = "overworld"
    g.help.close()
    inp = FakeInput(pressed={pygame.K_F1})
    g.input = inp
    SceneManager(g).run_frame(16)
    assert g.help.visible


def test_escape_opens_pause_same_frame(game):
    g = game
    g.scene = "overworld"
    g.pause.close()
    inp = FakeInput(pressed={pygame.K_ESCAPE})
    g.input = inp
    SceneManager(g).run_frame(16)
    assert g.pause.visible


def test_log_hidden_on_title(game):
    g = game
    g.scene = "title"
    inp = FakeInput()
    g.input = inp
    SceneManager(g).run_frame(16)
    log = g.windows.get("log")
    assert log is not None
    assert not log.visible
