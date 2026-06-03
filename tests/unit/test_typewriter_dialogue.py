"""Unit tests for Undertale-style typewriter dialogue."""
from src.ui.typewriter_dialogue import TypewriterDialogue


class SilentAudio:
    enabled = True
    blips: list[tuple[str, int]] = []

    def play_voice_blip(self, voice: str, variant: int = 0, **kwargs):
        SilentAudio.blips.append((voice, variant))


def test_typewriter_reveals_chars_over_time():
    tw = TypewriterDialogue()
    tw.open(["abc"], "default")
    assert tw.visible_text() == ""
    tw.update(40, None)
    assert tw.visible_text() == "a"
    tw.update(40, None)
    assert tw.visible_text() == "ab"


def test_typewriter_blips_skip_spaces():
    SilentAudio.blips = []
    tw = TypewriterDialogue()
    tw.open(["a b"], "elion")
    for _ in range(10):
        tw.update(40, SilentAudio())
    assert ("elion", 0) in SilentAudio.blips
    assert len([b for b in SilentAudio.blips if b[0] == "elion"]) == 2


def test_advance_completes_line_then_next():
    tw = TypewriterDialogue()
    tw.open(["one", "two"], "default")
    assert tw.advance() is False
    assert tw.visible_text() == "one"
    assert tw.advance() is False
    assert tw.line_idx == 1
    assert tw.advance() is False
    assert tw.visible_text() == "two"
    assert tw.advance() is True
