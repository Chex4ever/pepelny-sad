"""Tests for lighting and weather."""
from src.constants import DAY_CYCLE_TURNS
from src.world.lighting import ambient_for_turn, sky_char, torch_char, torch_flicker
from src.world.pepel_weather import PepelWeather


def test_ambient_higher_at_day_than_night():
    day = ambient_for_turn(DAY_CYCLE_TURNS // 2, "surface")
    night = ambient_for_turn(int(DAY_CYCLE_TURNS * 0.9), "surface")
    assert day > night


def test_dungeon_ambient_low():
    assert ambient_for_turn(0, "dungeon") < ambient_for_turn(0, "surface")


def test_torch_flicker_varies():
    values = {round(torch_flicker(i), 2) for i in range(20)}
    assert len(values) > 1


def test_torch_char_alternates():
    assert torch_char(0) != torch_char(4)


def test_sky_char_changes_over_cycle():
    chars = {sky_char(int(DAY_CYCLE_TURNS * p)) for p in (0.1, 0.5, 0.9)}
    assert len(chars) >= 2


def test_pepel_weather_cycles():
    weather = PepelWeather(42)
    saw_active = False
    for _ in range(100):
        active, penalty = weather.on_turn(False)
        saw_active = saw_active or active
        if active:
            assert penalty == 2
    assert saw_active


def test_pepel_shelter_no_fov_penalty():
    weather = PepelWeather(42)
    for _ in range(30):
        weather.on_turn(False)
    active, penalty = weather.on_turn(True)
    if active:
        assert penalty == 0
