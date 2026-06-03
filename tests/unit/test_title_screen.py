"""Tests for title screen background."""
from src.constants import SCREEN_H, SCREEN_W
from src.render.screen_buffer import ScreenBuffer
from src.ui.title_screen import TitleScreen


def test_title_screen_draws_garden_and_ash():
    buf = ScreenBuffer(SCREEN_W, SCREEN_H)
    screen = TitleScreen()
    screen.draw(buf, seed=42, frame=60, title_seed=42)

    chars = set(buf.chars)
    assert "," in chars or "." in chars  # ground
    assert any(c in chars for c in (":", "·", "."))  # ash
    assert "T" in chars or "~" in chars  # garden silhouette
    assert "l" in chars or "i" in chars  # torch on menu frame


def test_title_screen_animates_with_frame():
    buf1 = ScreenBuffer(SCREEN_W, SCREEN_H)
    buf2 = ScreenBuffer(SCREEN_W, SCREEN_H)
    screen = TitleScreen()
    screen.draw(buf1, seed=7, frame=0, title_seed=7)
    screen.draw(buf2, seed=7, frame=120, title_seed=7)
    assert buf1.chars != buf2.chars
