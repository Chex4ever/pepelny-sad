"""Input state per frame."""
from __future__ import annotations

import pygame

from src.constants import CELL_H, CELL_W

# SDL2 scancodes — physical key positions, layout-independent (QWERTY).
SCAN_ESCAPE = 41
SCAN_F1 = 58
SCAN_F5 = 62
SCAN_F9 = 67
SCAN_W, SCAN_A, SCAN_S, SCAN_D = 26, 4, 22, 7
SCAN_UP, SCAN_DOWN, SCAN_LEFT, SCAN_RIGHT = 82, 81, 80, 79
SCAN_E = 8
SCAN_TAB = 43
SCAN_RETURN = 40
SCAN_SPACE = 44


class InputState:
    def __init__(self):
        self.quit = False
        self.keys_down: set[int] = set()
        self.keys_pressed: set[int] = set()
        self.scancodes_down: set[int] = set()
        self.scancodes_pressed: set[int] = set()
        self.mouse_pos = (0, 0)
        self.mouse_pressed: set[int] = set()
        self._prev_keys = None

    def begin_frame(self):
        self.keys_pressed.clear()
        self.scancodes_pressed.clear()
        self.mouse_pressed.clear()

    def _normalize_key(self, event: pygame.event.Event) -> int | None:
        if event.type not in (pygame.KEYDOWN, pygame.KEYUP):
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
            sc = getattr(event, "scancode", 0)
            if sc:
                self.scancodes_down.add(sc)
                self.scancodes_pressed.add(sc)
        elif event.type == pygame.KEYUP:
            key = self._normalize_key(event)
            if key is not None:
                self.keys_down.discard(key)
            sc = getattr(event, "scancode", 0)
            if sc:
                self.scancodes_down.discard(sc)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_pos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_pressed.add(event.button)
        elif event.type == pygame.WINDOWFOCUSGAINED:
            pygame.event.clear(pygame.KEYDOWN)

    def sync_keyboard(self):
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

    def mouse_grid(self, char_w=CELL_W, char_h=CELL_H) -> tuple[int, int]:
        x, y = self.mouse_pos
        return x // char_w, y // char_h

    def mouse_world(self, camera_x: int, camera_y: int, map_origin_y: int = 1) -> tuple[int, int] | None:
        gx, gy = self.mouse_grid()
        from src.constants import MAP_VIEW_W, MAP_VIEW_H

        if gx < 0 or gx >= MAP_VIEW_W:
            return None
        local_y = gy - map_origin_y
        if local_y < 0 or local_y >= MAP_VIEW_H:
            return None
        return camera_x + gx, camera_y + local_y

    def mouse_left_clicked(self) -> bool:
        return 1 in self.mouse_pressed

    def pressed(self, key) -> bool:
        return key in self.keys_pressed

    def held(self, key) -> bool:
        return key in self.keys_down

    def scancode_pressed(self, *scancodes: int) -> bool:
        return any(sc in self.scancodes_pressed for sc in scancodes)

    def scancode_held(self, scancode: int) -> bool:
        return scancode in self.scancodes_down

    def any_pressed(self, *keys) -> bool:
        return any(k in self.keys_pressed for k in keys)

    def any_key_pressed(self) -> bool:
        return bool(self.keys_pressed) or bool(self.scancodes_pressed)

    def pressed_escape(self) -> bool:
        return self.any_pressed(pygame.K_ESCAPE) or self.scancode_pressed(SCAN_ESCAPE)

    def pressed_f1(self) -> bool:
        return self.any_pressed(pygame.K_F1) or self.scancode_pressed(SCAN_F1)

    def pressed_tab(self) -> bool:
        return self.any_pressed(pygame.K_TAB) or self.scancode_pressed(SCAN_TAB)

    def pressed_e(self) -> bool:
        return self.any_pressed(pygame.K_e) or self.scancode_pressed(SCAN_E)

    def pressed_f5(self) -> bool:
        return self.any_pressed(pygame.K_F5) or self.scancode_pressed(SCAN_F5)

    def pressed_f9(self) -> bool:
        return self.any_pressed(pygame.K_F9) or self.scancode_pressed(SCAN_F9)

    def nav_up_pressed(self) -> bool:
        return self.any_pressed(pygame.K_UP, pygame.K_w) or self.scancode_pressed(SCAN_UP, SCAN_W)

    def nav_down_pressed(self) -> bool:
        return self.any_pressed(pygame.K_DOWN, pygame.K_s) or self.scancode_pressed(SCAN_DOWN, SCAN_S)

    def nav_left_pressed(self) -> bool:
        return self.any_pressed(pygame.K_LEFT, pygame.K_a) or self.scancode_pressed(SCAN_LEFT, SCAN_A)

    def nav_right_pressed(self) -> bool:
        return self.any_pressed(pygame.K_RIGHT, pygame.K_d) or self.scancode_pressed(SCAN_RIGHT, SCAN_D)

    def nav_up_held(self) -> bool:
        return self.held(pygame.K_UP) or self.held(pygame.K_w) or self.scancode_held(SCAN_UP) or self.scancode_held(SCAN_W)

    def nav_down_held(self) -> bool:
        return self.held(pygame.K_DOWN) or self.held(pygame.K_s) or self.scancode_held(SCAN_DOWN) or self.scancode_held(SCAN_S)

    def nav_left_held(self) -> bool:
        return self.held(pygame.K_LEFT) or self.held(pygame.K_a) or self.scancode_held(SCAN_LEFT) or self.scancode_held(SCAN_A)

    def nav_right_held(self) -> bool:
        return self.held(pygame.K_RIGHT) or self.held(pygame.K_d) or self.scancode_held(SCAN_RIGHT) or self.scancode_held(SCAN_D)

    def confirm_pressed(self) -> bool:
        return self.action_pressed() or bool(self.mouse_pressed)

    def action_pressed(self) -> bool:
        return (
            self.any_pressed(pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
            or self.scancode_pressed(SCAN_RETURN, SCAN_SPACE)
        )

    def dir_key(self):
        if self.nav_up_pressed():
            return (0, -1)
        if self.nav_down_pressed():
            return (0, 1)
        if self.nav_left_pressed():
            return (-1, 0)
        if self.nav_right_pressed():
            return (1, 0)
        return None
