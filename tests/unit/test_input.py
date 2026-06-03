"""Tests for input handling."""
import pygame

from src.input import InputState


def test_key_press_and_release():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
    assert inp.pressed(pygame.K_w)
    assert inp.held(pygame.K_w)
    inp.begin_frame()
    assert not inp.pressed(pygame.K_w)
    assert inp.held(pygame.K_w)
    inp.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_w))
    assert not inp.held(pygame.K_w)


def test_dir_key_from_wasd():
    inp = InputState()
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    assert inp.dir_key() == (1, 0)


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
