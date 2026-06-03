"""Unit tests for dialogue voice mapping."""
from src.story.voices import default_voice, intro_voice, voice_for_dialogue


def test_default_voice_fallback():
    assert voice_for_dialogue("unknown_id") == default_voice()


def test_elder_has_own_voice():
    assert voice_for_dialogue("elder_intro") == "elder"


def test_intro_voice_is_elion():
    assert intro_voice() == "elion"
