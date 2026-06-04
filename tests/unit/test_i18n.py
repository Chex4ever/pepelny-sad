"""Tests for i18n loader."""
from src.data.art_loader import load_items
from src.i18n import localized_name, set_locale, t, t_list


def test_i18n_ru_default():
    set_locale("ru")
    assert "ход" in t_list("ui.help.lines")[0]


def test_i18n_en_help_line():
    set_locale("en")
    assert "move" in t_list("ui.help.lines")[0].lower()
    set_locale("ru")


def test_i18n_fallback_to_key():
    set_locale("ru")
    assert t("nonexistent.key.xyz") == "nonexistent.key.xyz"


def test_item_name_localized():
    set_locale("en")
    entry = load_items()["grey_tincture"]
    assert localized_name(entry, "grey_tincture", "item") == "Grey Tincture"
    set_locale("ru")


def test_dialogue_speaker_elder():
    from src.story.dialogues import get_dialogue, get_dialogue_speaker

    set_locale("ru")
    assert get_dialogue_speaker("elder_intro") == "Старейшина пепла"
    assert "Элион" in get_dialogue("elder_intro")[0]
