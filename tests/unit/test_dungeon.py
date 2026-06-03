"""Tests for dungeon stitcher and reskin."""
from src.world.dungeon_reskin import bullet_speed_mult, reskin_char
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.segment_loader import stitch_dungeon


def test_stitch_dungeon_is_deterministic(world_state):
    a = stitch_dungeon(world_state.world_seed)
    b = stitch_dungeon(world_state.world_seed)
    assert [s["name"] for s in a] == [s["name"] for s in b]


def test_stitch_has_five_segments():
    chain = stitch_dungeon(123)
    assert len(chain) == 5


def test_ensure_dungeon_populates_tiles(world_state, world_map):
    ensure_dungeon(world_state, world_map)
    assert len(world_map.dungeon_tiles) > 0
    assert world_state.dungeon_graph is not None


def test_reskin_peaceful(world_state):
    ch, color = reskin_char("░", spare_count=3, kill_count=0)
    assert ch == "*"
    assert color is not None


def test_bullet_speed_higher_on_kill_path(world_state):
    world_state.kill_count = 5
    world_state.spare_count = 0
    mult = bullet_speed_mult(world_state.kill_count, world_state.spare_count, True)
    assert mult == 1.1
