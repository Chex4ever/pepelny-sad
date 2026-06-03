"""Checkpoint save/load."""
from __future__ import annotations

import pickle
import os


SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "save.pkl")


def save_game(state: dict):
    with open(SAVE_PATH, "wb") as f:
        pickle.dump(state, f)


def load_game() -> dict | None:
    if not os.path.isfile(SAVE_PATH):
        return None
    with open(SAVE_PATH, "rb") as f:
        return pickle.load(f)
