"""Tests for companions and narrative."""
from src.story.narrative import ENDINGS, pick_ending
from src.world.companions import has_service, spawn_companion
from src.data.art_loader import load_enemies


def test_spawn_companion_on_spare(world_state):
    spawn_companion(world_state, "whisper", load_enemies())
    assert "whisper_companion" in world_state.companions
    assert world_state.spare_count == 1


def test_spawn_companion_idempotent(world_state):
    enemies = load_enemies()
    spawn_companion(world_state, "whisper", enemies)
    spawn_companion(world_state, "whisper", enemies)
    assert world_state.companions.count("whisper_companion") == 1


def test_has_service_mobile_forge(world_state):
    world_state.companions.append("whisper_companion")
    assert has_service(world_state.companions, "mobile_forge")


def test_pick_mercy_ending(world_state):
    world_state.spare_count = 2
    assert pick_ending(world_state, "spare") == "mercy"


def test_pick_kill_ending(world_state):
    assert pick_ending(world_state, "kill") == "kill"
    assert ENDINGS["kill"]["title"]
