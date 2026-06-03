"""Tests for architecture refactor helpers."""
from src.core.camera import Camera
from src.input import InputState
from src.render.screen_buffer import ScreenBuffer
from src.ui.windows.examine_window import ExamineWindow
from src.ui.windows.window_manager import WindowManager


def test_camera_view_origin_and_pan():
    from src.constants import MAP_VIEW_H

    cam = Camera(100, MAP_VIEW_H, pan_limit=10)
    cam.center_on(50, 50)
    assert cam.view_origin() == (0, 50 - MAP_VIEW_H // 2)
    cam.pan_by(3, -2)
    assert cam.view_origin() == (3, 50 - MAP_VIEW_H // 2 - 2)
    cam.reset_pan()
    assert cam.view_origin() == (0, 50 - MAP_VIEW_H // 2)


def test_camera_pan_clamped():
    cam = Camera(20, 20, pan_limit=5)
    cam.center_on(0, 0)
    cam.pan_by(20, -20)
    assert cam.pan_x == 5
    assert cam.pan_y == -5


def test_fill_rect_overwrites_cells():
    from src.render.screen_buffer import FOG_EXPLORED

    buf = ScreenBuffer(10, 10)
    buf.clear(bg=(1, 1, 1))
    buf.set_fog(2, 2, FOG_EXPLORED)
    buf.fill_rect(2, 2, 4, 3, bg=(99, 99, 99))
    assert buf.bg[buf._idx(2, 2)] == (99, 99, 99)
    assert buf.fog[buf._idx(2, 2)] == 0
    assert buf.fog_a[buf._idx(2, 2)] == 0


def test_examine_window_has_opaque_background(screen_buffer):
    w = ExamineWindow()
    w.show("elion")
    w.draw(screen_buffer)
    cx, cy, cw, ch = w.content_rect()
    assert screen_buffer.bg[screen_buffer._idx(cx + 1, cy + 1)] != (8, 8, 18)


def test_window_manager_z_order_focus():
    wm = WindowManager()
    a = ExamineWindow()
    a.name = "a"
    b = ExamineWindow()
    b.name = "b"
    wm.register(a)
    wm.register(b)
    wm.focus(a)
    assert wm._windows[-1] is a


def test_window_drag_clamps_position():
    from src.constants import MAP_ORIGIN_Y, MAP_VIEW_H
    from src.ui.windows.base import ModalWindow, buf_safe_max_x, buf_safe_max_y

    assert buf_safe_max_x(26, 200) == 74  # SCREEN_W=100
    w = ModalWindow("LOG", x=72, y=1, w=26, h=14, visible=True)
    w._dragging = True
    w._drag_off = (2, 0)

    class DragInput:
        def mouse_grid(self):
            return (80, 5)

        def mouse_left_held(self):
            return True

        def mouse_left_down(self):
            return False

        def mouse_left_released(self):
            return False

    consumed = w.handle_input(DragInput(), 80, 5)
    assert consumed
    assert 0 <= w.x <= 74
    assert buf_safe_max_y(14, 50) == MAP_ORIGIN_Y + MAP_VIEW_H - 14


def test_input_mouse_drag_detection():
    inp = InputState()
    inp.begin_frame()
    inp.mouse_down.add(1)
    inp._drag_start = (0, 0)
    inp.mouse_pos = (10, 10)
    assert inp.mouse_dragging(4)
