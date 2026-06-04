"""Story dialogues — localized via src/i18n."""
from __future__ import annotations

from src.i18n import t, t_list

SPEAKER_KEY_BY_DIALOGUE: dict[str, str] = {
    "elder_intro": "dialogue.speaker.elder",
    "ivy_crossing": "dialogue.speaker.narrator",
    "whisper_companion": "dialogue.speaker.whisper",
    "sorrow_companion": "dialogue.speaker.sorrow",
    "warden_mercy": "dialogue.speaker.warden",
    "warden_kill": "dialogue.speaker.warden",
}


def get_dialogue_speaker(dialogue_id: str) -> str:
    key = SPEAKER_KEY_BY_DIALOGUE.get(dialogue_id, "dialogue.speaker.narrator")
    return t(key)


def get_dialogue(dialogue_id: str) -> list[str]:
    lines = t_list(f"dialogue.{dialogue_id}.lines")
    if lines:
        return lines
    return [t("dialogue.speaker.narrator")]
