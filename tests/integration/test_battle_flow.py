"""Integration tests for battle flow."""
import pytest
import pygame

from src.battle.battle_scene import BattleScene
from tests.conftest import FakeInput


@pytest.mark.integration
def test_whisper_mercy_flow(profile, world_state):
    results = []

    battle = BattleScene("whisper", profile, world_state, results.append)
    battle.phase = BattleScene.PHASE_MENU
    battle.menu_cursor = 1  # Act

    # Perform act "Назвать Лиру" (index 1) which unlocks mercy.
    battle.phase = BattleScene.PHASE_ACT
    battle.act_cursor = 1
    battle.handle_input(FakeInput(pressed={pygame.K_RETURN}))

    assert "unlock_mercy" in battle.scan_flags
    assert battle.phase == BattleScene.PHASE_DODGE

    # Skip dodge phase quickly.
    battle.phase = BattleScene.PHASE_MENU
    battle.menu_cursor = 3  # Mercy
    battle.handle_input(FakeInput(pressed={pygame.K_RETURN}))

    assert battle.phase == BattleScene.PHASE_END
    assert battle.result == "spare"
    battle.handle_input(FakeInput(pressed={pygame.K_RETURN}))
    assert results == ["spare"]
    assert "whisper_companion" in world_state.companions


@pytest.mark.integration
def test_scan_unlocks_recipe_for_craft(profile, world_state):
    from src.progression.crafting import can_craft

    battle = BattleScene("whisper", profile, world_state, lambda _: None)
    battle.phase = BattleScene.PHASE_ACT
    battle.act_cursor = 0  # listen -> grey_tincture
    battle.handle_input(FakeInput(pressed={pygame.K_RETURN}))

    assert "grey_tincture" in world_state.discovered_recipes
    assert can_craft(
        "grey_tincture",
        profile.inventory,
        world_state.discovered_recipes,
        world_state.scan_flags,
    )


@pytest.mark.integration
def test_battle_intro_to_menu(profile, world_state):
    battle = BattleScene("sorrow", profile, world_state, lambda _: None)
    assert battle.phase == BattleScene.PHASE_INTRO
    for _ in range(100):
        battle.update()
    assert battle.phase == BattleScene.PHASE_MENU


@pytest.mark.integration
def test_battle_draw_no_crash(profile, world_state, screen_buffer):
    battle = BattleScene("warden", profile, world_state, lambda _: None)
    battle.draw(screen_buffer)
    assert any(ch != " " for ch in screen_buffer.chars)


@pytest.mark.integration
def test_wide_greaves_expands_dodge_box(profile, world_state):
    profile.equipment.equip("legs", "root_greaves")
    battle = BattleScene("whisper", profile, world_state, lambda _: None)
    assert battle.box_w == 40.0
