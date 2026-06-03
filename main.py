"""Пепельный Сад — entry point."""
import os

# Real display/input: dummy SDL from pytest must not leak into gameplay.
for _var in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER"):
    if os.environ.get(_var) == "dummy":
        os.environ.pop(_var)

from src.constants import init_paths

init_paths(os.path.dirname(os.path.abspath(__file__)))

from src.game import main

if __name__ == "__main__":
    main()
