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
    start = game.overworld.player.tile_pos()
    game.overworld.handle_input(FakeInput(pressed={pygame.K_d}), dt_ms=250)
    game.overworld.update_deferred()
    assert game.overworld.player.tile_pos() != start
    assert len(mock.footsteps) >= 1


@pytest.mark.integration
def test_pickup_plays_sfx(game):
    mock = MockAudio()
    game.audio = mock
    px, py = game.overworld.player.tile_pos()
    layer = game.world_state.layer
    game.world_map.set_dungeon_tile(px + 1, py, "o") if layer == "dungeon" else None
    if layer == "surface":
        cx, cy, lx, ly = game.world_map.world_to_chunk(px + 1, py)
        chunk = game.world_map.chunks[(cx, cy)]
        chunk.set(lx, ly, "o")
    game.overworld.player.set_tile(px + 1, py)
    game.overworld.handle_input(FakeInput(pressed={pygame.K_e}))
    assert "pickup" in mock.sfx
