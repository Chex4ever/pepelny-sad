"""Unit tests for UX/render overhaul."""
import pygame

from src.constants import CELL_H, CELL_W, MAP_VIEW_H, MAP_VIEW_W
from src.input import InputState
from src.render.light_map import LightMap
from src.render.screen_buffer import ScreenBuffer
from src.ui.title_screen import TitleScreen
from src.world.visibility import EXPLORED, UNEXPLORED, VISIBLE, filter_tile_char


def test_filter_tile_hides_entities_when_explored():
    assert filter_tile_char("!", EXPLORED) == "."
    assert filter_tile_char("!", VISIBLE) == "!"
    assert filter_tile_char("$", EXPLORED) == "."
    assert filter_tile_char("@", EXPLORED) == "."
    assert filter_tile_char("T", EXPLORED) == "T"
    assert filter_tile_char(".", UNEXPLORED) is None


def test_light_map_radial_falloff():
    lm = LightMap(9, 9)
    lm.clear(0.2)
    lm.add_source(4, 4, 3.0, 0.8)
    center = lm.get(4, 4)
    edge = lm.get(0, 0)
    assert center > edge
    assert center > 0.5


def test_mouse_grid_maps_pixels():
    inp = InputState()
    inp.mouse_pos = (CELL_W * 3 + 2, CELL_H * 5 + 1)
    gx, gy = inp.mouse_grid(CELL_W, CELL_H)
    assert gx == 3
    assert gy == 5


def test_mouse_world_respects_map_bounds():
    inp = InputState()
    inp.mouse_pos = (0, CELL_H * 2)
    assert inp.mouse_world(10, 20, map_origin_y=0) == (10, 22)
    inp.mouse_pos = (MAP_VIEW_W * CELL_W + 10, CELL_H)
    assert inp.mouse_world(0, 0, map_origin_y=0) is None


def test_title_phases_progress():
    from src.constants import SCREEN_H, SCREEN_W

    buf_early = ScreenBuffer(SCREEN_W, SCREEN_H)
    buf_late = ScreenBuffer(SCREEN_W, SCREEN_H)
    screen = TitleScreen()
    screen.draw(buf_early, seed=1, elapsed_ms=200, title_seed=1)
    screen.draw(buf_late, seed=1, elapsed_ms=4500, title_seed=1)
    assert buf_early.chars != buf_late.chars


def test_intro_skip_advances_lines():
    from src.story.intro import INTRO_LINES, IntroScene
    from tests.conftest import FakeInput

    intro = IntroScene()
    intro.reset()
    inp = FakeInput(pressed={pygame.K_RETURN})
    for _ in range(len(INTRO_LINES)):
        intro.writer.complete_line()
        if intro.handle_input(inp):
            break
    assert intro.done


def test_intro_accepts_mouse_click():
    from src.story.intro import IntroScene
    from tests.conftest import FakeInput

    intro = IntroScene()
    intro.reset()
    class ClickInput(FakeInput):
        def confirm_pressed(self):
            return True

    intro.writer.complete_line()
    assert intro.handle_input(ClickInput()) is False
    assert intro.line_idx == 1
