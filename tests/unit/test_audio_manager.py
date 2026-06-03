"""Unit tests for AudioManager disabled/no-op mode."""
from src.audio.audio_manager import AudioManager


def test_audio_manager_disabled_without_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    mgr = AudioManager()
    assert mgr.init(str(tmp_path)) is False
    assert mgr.enabled is False
    assert mgr.play_sfx("ui_confirm") is False
    assert mgr.play_footstep("grass") is False


def test_footstep_cooldown():
    mgr = AudioManager()
    mgr.enabled = True
    mgr._groups["footstep_grass"] = ["footstep_grass_low_0"]
    mgr._manifest["footstep_grass_low_0"] = {"volume": 0.5}
    mgr._last_footstep_ms = 999999999
    assert mgr.play_footstep("grass") is False
