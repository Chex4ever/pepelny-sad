"""Tile visibility states and entity filtering."""
from __future__ import annotations

VISIBLE = "visible"
EXPLORED = "explored"
UNEXPLORED = "unexplored"

_ENTITY_CHARS = frozenset("!$@")
_TERRAIN_FALLBACK = {
    "!": ".",
    "$": ".",
    "@": ".",
}


def visibility_state(wx: int, wy: int, visible: set[tuple[int, int]], is_explored) -> str:
    if (wx, wy) in visible:
        return VISIBLE
    if is_explored(wx, wy):
        return EXPLORED
    return UNEXPLORED


def filter_tile_char(ch: str, state: str) -> str | None:
    """Return char to draw, or None for full black fog."""
    if state == UNEXPLORED:
        return None
    if state == VISIBLE:
        return ch
    if ch in _ENTITY_CHARS:
        return _TERRAIN_FALLBACK.get(ch, ".")
    return ch


def blocks_los(ch: str) -> bool:
    return ch in "#T░▒▓│─┌┐└┘"
