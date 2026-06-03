"""Integration tests for audio hooks."""
import pytest
import pygame

from tests.conftest import FakeInput


class MockAudio:
    def __init__(self):
        self.enabled = True
        self.footsteps: list[str] = []
        self.sfx: list[str] = []

    def play_footstep(self, surface: str) -> bool:
        self.footsteps.append(surface)
        return True

    def play_sfx(self, sound_id: str, volume: float = 1.0) -> bool:
        self.sfx.append(sound_id)
        return True


@pytest.mark.integration
def test_movement_plays_footstep(game):
    mock = MockAudio()
    game.audio = mock
    game.overworld.update()
    start = (game.overworld.player.x, game.overworld.player.y)
    game.overworld.handle_input(FakeInput(pressed={pygame.K_d}))
    assert (game.overworld.player.x, game.overworld.player.y) != start
    assert len(mock.footsteps) >= 1


@pytest.mark.integration
def test_pickup_plays_sfx(game):
    mock = MockAudio()
    game.audio = mock
    px, py = game.overworld.player.x, game.overworld.player.y
    layer = game.world_state.layer
    game.world_map.set_dungeon_tile(px + 1, py, "o") if layer == "dungeon" else None
    if layer == "surface":
        cx, cy, lx, ly = game.world_map.world_to_chunk(px + 1, py)
        chunk = game.world_map.chunks[(cx, cy)]
        chunk.set(lx, ly, "o")
    game.overworld.player.x = px + 1
    game.overworld.handle_input(FakeInput(pressed={pygame.K_e}))
    assert "pickup" in mock.sfx
