"""Editor UI fonts: Cyrillic labels + transport icons with fallbacks."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

_UI_CACHE: dict[int, pygame.font.Font] = {}
_MONO_CACHE: dict[int, pygame.font.Font] = {}
_ICON_CACHE: dict[int, tuple[pygame.font.Font, TransportIcons]] = {}

UI_FAMILIES = "segoe ui,arial,tahoma,dejavu sans"
MONO_FAMILIES = "consolas,courier new,cascadia mono"
ICON_FAMILIES = "segoe ui symbol,segoe mdl2 assets,arial unicode ms,dejavu sans"


@dataclass(frozen=True)
class TransportIcons:
    play: str
    pause: str
    prev: str
    next: str


UNICODE_TRANSPORT = TransportIcons(
    play="\u25b6",
    pause="\u23f8",
    prev="\u25c0",
    next="\u25b6",
)
ASCII_TRANSPORT = TransportIcons(
    play=">",
    pause="||",
    prev="<",
    next=">",
)


def editor_ui_font(size: int = 13) -> pygame.font.Font:
    """Labels and Cyrillic UI (Segoe UI stack)."""
    if size not in _UI_CACHE:
        _ensure_font_init()
        _UI_CACHE[size] = pygame.font.SysFont(UI_FAMILIES, size)
    return _UI_CACHE[size]


def editor_mono_font(size: int = 10) -> pygame.font.Font:
    """Numeric paths / diff values."""
    if size not in _MONO_CACHE:
        _ensure_font_init()
        _MONO_CACHE[size] = pygame.font.SysFont(MONO_FAMILIES, size)
    return _MONO_CACHE[size]


def transport_icon_font(size: int = 11) -> tuple[pygame.font.Font, TransportIcons]:
    """Font + play/pause/prev/next glyphs guaranteed to render."""
    if size not in _ICON_CACHE:
        _ensure_font_init()
        _ICON_CACHE[size] = _resolve_icon_font(size)
    return _ICON_CACHE[size]


def glyph_render_size(font: pygame.font.Font, ch: str) -> tuple[int, int]:
    surf = font.render(ch, True, (255, 255, 255))
    return surf.get_width(), surf.get_height()


def _ensure_font_init() -> None:
    if not pygame.font.get_init():
        pygame.font.init()


def _icons_usable(font: pygame.font.Font, icons: TransportIcons) -> bool:
    play_w, _ = glyph_render_size(font, icons.play)
    pause_w, _ = glyph_render_size(font, icons.pause)
    prev_w, _ = glyph_render_size(font, icons.prev)
    if min(play_w, pause_w, prev_w) < 5:
        return False
    # Replacement glyphs in Segoe UI / Consolas are same width for all symbols.
    if play_w == pause_w == prev_w:
        return False
    return True


def _resolve_icon_font(size: int) -> tuple[pygame.font.Font, TransportIcons]:
    for family in ICON_FAMILIES.split(","):
        font = pygame.font.SysFont(family.strip(), size)
        if _icons_usable(font, UNICODE_TRANSPORT):
            return font, UNICODE_TRANSPORT
    font = pygame.font.SysFont(MONO_FAMILIES, size)
    return font, ASCII_TRANSPORT
