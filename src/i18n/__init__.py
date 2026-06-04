"""Internationalization — ru/en locale JSON."""
from src.i18n.loader import (
    get_locale,
    init_locale_from_env,
    localized_name,
    set_locale,
    t,
    t_list,
)

__all__ = [
    "t",
    "t_list",
    "get_locale",
    "set_locale",
    "init_locale_from_env",
    "localized_name",
]
