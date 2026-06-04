"""Load nested locale JSON and resolve translation keys."""
from __future__ import annotations

import json
import os
from functools import lru_cache

from src import constants

_DEFAULT_LANG = "ru"
_current_lang = _DEFAULT_LANG


def _locale_dir() -> str:
    base = constants.DATA_DIR or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "locale")


def get_locale() -> str:
    return _current_lang


def set_locale(lang: str) -> None:
    global _current_lang
    lang = (lang or _DEFAULT_LANG).lower().split("-")[0]
    if lang not in ("ru", "en"):
        lang = _DEFAULT_LANG
    _current_lang = lang
    _load_locale.cache_clear()


def init_locale_from_env() -> None:
    lang = os.environ.get("PEPELNY_LANG", _DEFAULT_LANG)
    set_locale(lang)


@lru_cache(maxsize=8)
def _load_locale(lang: str) -> dict:
    path = os.path.join(_locale_dir(), f"{lang}.json")
    if not os.path.isfile(path):
        if lang != _DEFAULT_LANG:
            return _load_locale(_DEFAULT_LANG)
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _lookup(data: dict, key: str) -> str | list | dict | None:
    node: object = data
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def t(key: str, **fmt: object) -> str:
    """Translate dot-key; fallback ru → key string."""
    for lang in (_current_lang, _DEFAULT_LANG):
        data = _load_locale(lang)
        val = _lookup(data, key)
        if isinstance(val, str):
            return val.format(**fmt) if fmt else val
    return key.format(**fmt) if fmt else key


def t_list(key: str) -> list[str]:
    for lang in (_current_lang, _DEFAULT_LANG):
        data = _load_locale(lang)
        val = _lookup(data, key)
        if isinstance(val, list):
            return [str(x) for x in val]
    return []


def localized_name(entry: dict, entry_id: str, category: str = "item") -> str:
    key = entry.get("name_key") or f"{category}.{entry_id}.name"
    text = t(key)
    if text != key:
        return text
    return entry.get("name", entry_id)
