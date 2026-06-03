"""Tests for input handling."""
import pygame

from src.input import InputState, SCAN_D, SCAN_RETURN, SCAN_W


def test_key_press_and_release():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w, scancode=SCAN_W))
    assert inp.pressed(pygame.K_w)
    assert inp.held(pygame.K_w)
    assert inp.scancode_pressed(SCAN_W)
    inp.begin_frame()
    assert not inp.pressed(pygame.K_w)
    assert inp.held(pygame.K_w)
    inp.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_w, scancode=SCAN_W))
    assert not inp.held(pygame.K_w)


def test_dir_key_from_wasd():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d, scancode=SCAN_D))
    assert inp.dir_key() == (1, 0)


def test_dir_key_from_scancode_on_russian_layout():
    """Physical W key on RU layout emits Cyrillic key code but same scancode."""
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=ord("ц"), scancode=SCAN_W))
    assert inp.dir_key() == (0, -1)


def test_escape_via_scancode():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, scancode=41))
    assert inp.pressed_escape()


def test_f1_via_scancode():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1, scancode=58))
    assert inp.pressed_f1()


def test_quit_on_window_close():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.QUIT))
    assert inp.quit


def test_confirm_includes_numpad_enter():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP_ENTER))
    assert inp.confirm_pressed()


def test_confirm_includes_mouse():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)))
    assert inp.confirm_pressed()


def test_sync_keyboard_after_keydown():
    inp = InputState()
    inp.sync_keyboard()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    assert inp.pressed(pygame.K_r)


def test_sync_populates_scancode_pressed(monkeypatch):
    """pygame-ce get_pressed() is scancode-indexed; sync must fill scancodes_pressed."""
    class _ScanView:
        __slots__ = ("active",)

        def __init__(self, active=frozenset()):
            self.active = active

        def __len__(self):
            return 512

        def __getitem__(self, sc):
            return sc in self.active

    held = _ScanView({SCAN_W, SCAN_RETURN})
    pressed = _ScanView({SCAN_W, SCAN_RETURN})
    released = _ScanView()

    monkeypatch.setattr("pygame.key.get_pressed", lambda: held)
    monkeypatch.setattr("pygame.key.get_just_pressed", lambda: pressed)
    monkeypatch.setattr("pygame.key.get_just_released", lambda: released)

    inp = InputState()
    inp.sync_keyboard()
    assert inp.dir_key() == (0, -1)
    assert inp.action_pressed()
    assert not inp.pressed(pygame.K_w)
