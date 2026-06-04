"""Dialogue box shows speaker name, not generic title."""
from src.story.dialogues import get_dialogue, get_dialogue_speaker
from src.ui.typewriter_dialogue import TypewriterDialogue


def test_dialogue_title_is_speaker_name():
    speaker = get_dialogue_speaker("elder_intro")
    lines = get_dialogue("elder_intro")
    dlg = TypewriterDialogue()
    dlg.open(lines, "elder", speaker)
    assert dlg.speaker == speaker
    assert not lines[0].startswith(speaker)


def test_strip_speaker_prefix_legacy():
    dlg = TypewriterDialogue()
    dlg.open(["Старейшина пепла: Привет."], "default", "Старейшина пепла")
    assert dlg.lines[0] == "Привет."
