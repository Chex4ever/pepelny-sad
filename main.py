"""Пепельный Сад — entry point."""
import os
import sys


def _maybe_auto_update() -> None:
    if not getattr(sys, "frozen", False):
        return
    from src.updater.manager import maybe_update, restart_if_needed

    restart_if_needed(maybe_update())


# Real display/input: dummy SDL from pytest must not leak into gameplay.
for _var in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER"):
    if os.environ.get(_var) == "dummy":
        os.environ.pop(_var)

_maybe_auto_update()

from src.constants import init_paths

init_paths(os.path.dirname(os.path.abspath(__file__)))

from src.i18n import init_locale_from_env

init_locale_from_env()

from src.game import main

if __name__ == "__main__":
    main()
