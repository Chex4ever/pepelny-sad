"""Tests for ScreenBuffer."""
from src.render.screen_buffer import ScreenBuffer


def test_set_and_get_in_bounds():
    buf = ScreenBuffer(10, 5)
    buf.set(3, 2, "X", fg=(1, 2, 3), bg=(4, 5, 6), light=0.5)
    assert buf.get(3, 2) == "X"
    assert buf.fg[buf._idx(3, 2)] == (1, 2, 3)
    assert buf.light[buf._idx(3, 2)] == 0.5


def test_set_out_of_bounds_is_noop():
    buf = ScreenBuffer(4, 4)
    buf.set(99, 99, "#")
    assert buf.get(0, 0) == " "


def test_draw_text_truncates_at_width():
    buf = ScreenBuffer(5, 3)
    buf.draw_text(1, 1, "HELLO WORLD")
    assert buf.get(1, 1) == "H"
    assert buf.get(5, 1) == " "


def test_draw_box_with_title():
    buf = ScreenBuffer(20, 10)
    buf.draw_box(2, 2, 8, 5, title="TEST")
    assert buf.get(2, 2) == "┌"
    assert buf.get(2, 3) == "│"


def test_blit_copies_region():
    src = ScreenBuffer(4, 4)
    dst = ScreenBuffer(6, 6)
    src.set(1, 1, "A")
    dst.blit(src, 2, 2)
    assert dst.get(3, 3) == "A"
