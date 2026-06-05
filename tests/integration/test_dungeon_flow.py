"""Integration tests for dungeon layer."""
import pytest

from src.world.dungeon_stitcher import ensure_dungeon


@pytest.mark.integration
def test_dungeon_layer_transition(game):
    game.world_state.layer = "dungeon"
    ensure_dungeon(game.world_state, game.world_map)
    game.overworld.player.set_tile(2, 2)

    ch, _, _ = game.world_map.get_tile(2, 2, "dungeon")
    assert ch != "░"
    game.overworld.draw(__import__("src.render.screen_buffer", fromlist=["ScreenBuffer"]).ScreenBuffer(100, 45))


@pytest.mark.integration
def test_dungeon_graph_cached(game):
    ensure_dungeon(game.world_state, game.world_map)
    graph1 = game.world_state.dungeon_graph
    ensure_dungeon(game.world_state, game.world_map)
    assert game.world_state.dungeon_graph is graph1
