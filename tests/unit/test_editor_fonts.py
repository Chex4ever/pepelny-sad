"""Editor font stacks — transport icons must render with distinct widths."""
from __future__ import annotations

import os

import pytest


@pytest.fixture
def editor_font_env():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    yield
    # keep pygame up for other tests in session


@pytest.mark.unit
def test_transport_icons_render_non_empty(editor_font_env):
    from src.characters.editor_fonts import (
        ASCII_TRANSPORT,
        UNICODE_TRANSPORT,
        glyph_render_size,
        transport_icon_font,
    )

    font, icons = transport_icon_font(11)
    assert icons in (UNICODE_TRANSPORT, ASCII_TRANSPORT)
    for label in (icons.play, icons.pause, icons.prev, icons.next):
        w, h = glyph_render_size(font, label)
        assert w >= 4, f"{label!r} width={w}"
        assert h >= 8, f"{label!r} height={h}"


@pytest.mark.unit
def test_transport_pause_differs_from_play(editor_font_env):
    from src.characters.editor_fonts import glyph_render_size, transport_icon_font

    font, icons = transport_icon_font(11)
    play_w, _ = glyph_render_size(font, icons.play)
    pause_w, _ = glyph_render_size(font, icons.pause)
    assert play_w != pause_w


@pytest.mark.unit
def test_segoe_ui_alone_is_not_used_for_unicode_icons(editor_font_env):
    """Segoe UI draws ▶/⏸ as same-width stubs — we must not pick it for icons."""
    import pygame

    from src.characters.editor_fonts import UNICODE_TRANSPORT, _icons_usable

    segoe = pygame.font.SysFont("segoe ui", 11)
    assert not _icons_usable(segoe, UNICODE_TRANSPORT)


@pytest.mark.unit
def test_editor_ui_font_cyrillic(editor_font_env):
    from src.characters.editor_fonts import editor_ui_font, glyph_render_size

    font = editor_ui_font(13)
    w, h = glyph_render_size(font, "Свет")
    assert w > 20
    assert h >= 10
