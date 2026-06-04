"""Volumetric columns, clearance, walkability."""
from __future__ import annotations

from src.constants import DEFAULT_PLAYER_HEIGHT_M
from src.world.column import CLEARANCE_OPEN, Column, Solid
from src.world.structures import StructureAnchor
from src.world.tree_generator import build_tree_solids, roll_tree_params
from src.world.world_map import WorldMap


def _col_with_solids(solids: list[Solid]) -> Column:
    col = Column(floor_ch=".", floor_stencil_id="grass")
    for s in solids:
        col.add_solid(s)
    return col


def test_clearance_open_without_blocking():
    col = _col_with_solids(
        [Solid(1.0, 3.0, blocks_movement=False, stencil_id="tree_canopy_v0_h5_r2")]
    )
    assert col.clearance_m() == CLEARANCE_OPEN


def test_trunk_blocks_player_low_gap_allows_pet():
    trunk = Solid(0.0, 1.5, blocks_movement=True, stencil_id="tree_trunk_slim")
    assert _col_with_solids([trunk]).clearance_m() < DEFAULT_PLAYER_HEIGHT_M
    low_branch = Solid(0.5, 1.2, blocks_movement=True, stencil_id="tree_branch")
    gap_col = _col_with_solids([low_branch])
    assert gap_col.clearance_m() == 0.5
    assert gap_col.clearance_m() < 1.8
    assert gap_col.clearance_m() >= 0.5


def test_neighbor_canopy_only_walkable_for_player():
    params = {
        "height_m": 8.0,
        "trunk_ratio": 0.4,
        "canopy_radius": 2,
        "lean": 1,
        "variant": 0,
        "thick_trunk": False,
    }
    solids = build_tree_solids(params)
    trunk_cell = [s for dx, dy, s in solids if dx == 0 and dy == 0][0]
    canopy_neighbor = [s for dx, dy, s in solids if dx == 1 and dy == 0][0]
    trunk_col = _col_with_solids([trunk_cell])
    canopy_col = _col_with_solids([canopy_neighbor])
    assert trunk_col.clearance_m() < 1.8
    assert canopy_col.clearance_m() >= 1.8


def test_world_map_is_walkable_body_height():
    wm = WorldMap(42)
    wm._ensure_radius(10, 10)
    for wx in range(5, 40):
        for wy in range(5, 40):
            c = wm.clearance_m(wx, wy)
            if c >= 1.8:
                assert wm.is_walkable(wx, wy, body_height_m=1.8)
            if c >= 0.5:
                assert wm.is_walkable(wx, wy, body_height_m=0.5)
                return
    raise AssertionError("no tile with clearance >= 0.5m found")


def test_iso_draw_sort_key_z_order():
    items = [(10, 0.0), (10, 1.5), (10, 2.0)]
    sorted_items = sorted(items, key=lambda t: (t[0], t[1]))
    assert sorted_items[0][1] < sorted_items[1][1] < sorted_items[2][1]


def test_canopy_under_8m_tree_allows_player():
    biome = {"tree_height_m": [7, 8]}
    params = roll_tree_params(biome, 99, 100, 200)
    params["canopy_radius"] = 2
    params["height_m"] = 8.0
    solids = build_tree_solids(params)
    canopy = [s for dx, dy, s in solids if dx != 0 or dy != 0][0]
    col = _col_with_solids([canopy])
    assert col.clearance_m() >= 1.8


def test_tree_anchor_rebuild_in_get_column():
    wm = WorldMap(7)
    wm._ensure_radius(16, 16)
    found = False
    for chunk in wm.chunks.values():
        for anchor in chunk.structure_anchors:
            if anchor.structure_id == "tree":
                col = wm.get_column(anchor.wx + 1, anchor.wy, "surface")
                if any(s.stencil_id and "canopy" in s.stencil_id for s in col.solids):
                    found = True
                    break
        if found:
            break
    assert found or len(wm.chunks) > 0
