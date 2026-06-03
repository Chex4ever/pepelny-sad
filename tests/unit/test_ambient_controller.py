"""Unit tests for ambient volume logic."""
from src.audio.ambient_controller import nearest_torch_volume


def test_torch_volume_at_distance():
    visible = {(5, 5), (10, 10)}
    tile_ch = lambda x, y: "l" if (x, y) == (10, 10) else "."
    vol_near = nearest_torch_volume(visible, (9, 10), tile_ch)
    vol_far = nearest_torch_volume(visible, (0, 0), tile_ch)
    assert vol_near > vol_far
    assert vol_near > 0.5


def test_torch_volume_no_torches():
    assert nearest_torch_volume({(1, 1)}, (1, 1), lambda x, y: ".") == 0.0
