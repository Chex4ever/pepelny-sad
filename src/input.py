"""Input state per frame."""
from __future__ import annotations

import pygame


class InputState:
    def __init__(self):
        self.quit = False
        self.keys_down: set[int] = set()
        self.keys_pressed: set[int] = set()
        self.mouse_pos = (0, 0)
        self.mouse_pressed: set[int] = set()
        self._prev_keys = None

    def begin_frame(self):
        self.keys_pressed.clear()
        self.mouse_pressed.clear()

    def _normalize_key(self, event: pygame.event.Event) -> int | None:
        if event.type != pygame.KEYDOWN:
            return None
        key = event.key
        if key == pygame.K_UNKNOWN:
            try:
                key = pygame.key.key_code(pygame.scancode_to_key(event.scancode))
            except (AttributeError, ValueError, TypeError):
                return None
        return key

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT:
            self.quit = True
        elif event.type == pygame.KEYDOWN:
            key = self._normalize_key(event)
            if key is not None:
                self.keys_down.add(key)
                self.keys_pressed.add(key)
            if event.key == pygame.K_ESCAPE:
                self.quit = False  # handled by scenes
        elif event.type == pygame.KEYUP:
            key = event.key
            if key == pygame.K_UNKNOWN:
                try:
                    key = pygame.key.key_code(pygame.scancode_to_key(event.scancode))
                except (AttributeError, ValueError, TypeError):
                    return
            self.keys_down.discard(key)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_pressed.add(event.button)
        elif event.type == pygame.WINDOWFOCUSGAINED:
            pygame.event.clear(pygame.KEYDOWN)

    def sync_keyboard(self):
        """Edge-detect via get_pressed(); works when KEYDOWN events are dropped."""
        current = pygame.key.get_pressed()
        if self._prev_keys is None:
            self._prev_keys = current
            return
        for key in range(len(current)):
            if current[key] and not self._prev_keys[key]:
                self.keys_down.add(key)
                self.keys_pressed.add(key)
            elif not current[key] and self._prev_keys[key]:
                self.keys_down.discard(key)
        self._prev_keys = current

    def pressed(self, key) -> bool:
        return key in self.keys_pressed

    def held(self, key) -> bool:
        return key in self.keys_down

    def any_pressed(self, *keys) -> bool:
        return any(k in self.keys_pressed for k in keys)

    def confirm_pressed(self) -> bool:
        """Enter / Space / numpad Enter / mouse click."""
        return self.action_pressed() or bool(self.mouse_pressed)

    def action_pressed(self) -> bool:
        return self.any_pressed(pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

    def dir_key(self):
        if self.any_pressed(pygame.K_UP, pygame.K_w):
            return (0, -1)
        if self.any_pressed(pygame.K_DOWN, pygame.K_s):
            return (0, 1)
        if self.any_pressed(pygame.K_LEFT, pygame.K_a):
            return (-1, 0)
        if self.any_pressed(pygame.K_RIGHT, pygame.K_d):
            return (1, 0)
        return None
