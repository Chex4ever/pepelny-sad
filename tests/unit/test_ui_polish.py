"""Tests for UI polish: window chrome, fog on UI, examine non-blocking."""
from src.render.screen_buffer import FOG_EXPLORED, ScreenBuffer
from src.ui.windows.base import ModalWindow
from src.ui.windows.examine_window import ExamineWindow


def test_window_close_button_does_not_overlap_corner():
    w = ModalWindow("TEST", x=10, y=5, w=20, h=8, visible=True)
    buf = ScreenBuffer(100, 45)
    w.draw_chrome(buf)
    assert buf.chars[buf._idx(w.x + w.w - 1, w.y)] == "┐"
    assert buf.chars[buf._idx(w.x + w.w - 2, w.y)] == "×"
    assert buf.chars[buf._idx(w.x + w.w - 4, w.y)] == "−"


def test_ui_fill_rect_clears_fog_overlay():
    w = ExamineWindow()
    w.show("elion")
    buf = ScreenBuffer(100, 45)
    buf.set_fog(62, 5, FOG_EXPLORED)
    w.draw(buf)
    cx, cy, _, _ = w.content_rect()
    assert buf.fog[buf._idx(cx + 1, cy + 1)] == 0


def test_examine_does_not_block_world_input():
    assert ExamineWindow.blocks_world_input is False
