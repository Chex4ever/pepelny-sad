"""Integration tests for game state and scenes."""
import pytest
import pygame

from src.battle.battle_scene import BattleScene
from src.world.save import load_game, save_game
from tests.conftest import FakeInput


@pytest.mark.integration
def test_new_game_initial_state(game):
    assert game.scene == "overworld"
    assert game.overworld is not None
    assert game.profile.inventory.has("grey_herb")
    assert game.world_state.world_seed == 4242


@pytest.mark.integration
def test_serialize_restore_roundtrip(game):
    game.overworld.player.x = 55
    game.overworld.player.y = 33
    game.profile.hp = 17
    game.world_state.companions.append("whisper_companion")
    data = game.serialize_state()

    game.restore_state(data)
    assert game.profile.hp == 17
    assert game.overworld.player.x == 55
    assert "whisper_companion" in game.world_state.companions


@pytest.mark.integration
def test_save_load_via_game_api(game, save_path):
    game.overworld.player.x = 40
    game.profile.hp = 12
    save_game(game.serialize_state())

    game2 = type(game)( )
    game2.restore_state(load_game())

    assert game2.profile.hp == 12
    assert game2.overworld.player.x == 40


@pytest.mark.integration
def test_overworld_update_and_draw(game, screen_buffer):
    game.overworld.update()
    game.overworld.draw(screen_buffer)
    assert any(ch == "@" for ch in screen_buffer.chars)


@pytest.mark.integration
def test_overworld_movement_changes_position(game):
    start = (game.overworld.player.x, game.overworld.player.y)
    game.overworld.handle_input(FakeInput(pressed={pygame.K_d}))
    assert (game.overworld.player.x, game.overworld.player.y) != start


@pytest.mark.integration
def test_battle_transition_from_overworld(game):
    game.overworld.pending_battle = "whisper"
    enemy = game.overworld.needs_battle
    assert enemy == "whisper"
    game.battle = BattleScene(enemy, game.profile, game.world_state, game._on_battle_done)
    game.scene = "battle"
    game.battle.phase = BattleScene.PHASE_END
    game.battle.result = "spare"
    game.battle.handle_input(FakeInput(pressed={pygame.K_RETURN}))
    assert game.scene == "overworld"
    assert game.battle is None


@pytest.mark.integration
def test_boss_battle_triggers_ending(game):
    game.enemy_id_boss = True
    game._on_battle_done("spare")
    assert game.scene == "ending"
    assert game.ending_data is not None
