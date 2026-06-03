"""Tests for input handling."""
import pygame

from src.input import InputState, SCAN_D, SCAN_W


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
