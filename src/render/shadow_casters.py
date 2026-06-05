"""Collect shadow casters from world columns and entities."""
from __future__ import annotations

from src.constants import DEFAULT_PLAYER_HEIGHT_M
from src.render.shadow_map import ShadowCaster
from src.world.column import Column
from src.world.visibility import UNEXPLORED, visibility_state

_WALL_CHARS = frozenset("#░▒▓│─┌┐└┘")


def column_caster_height(col: Column) -> float:
    if col.floor_ch in _WALL_CHARS:
        return 2.8
    if col.floor_stencil_id in ("forge", "elder_station"):
        return 2.2
    height = 0.0
    for solid in col.solids:
        sid = solid.stencil_id or ""
        z_top = solid.z_max
        if "trunk" in sid or solid.blocks_movement:
            height = max(height, z_top)
        elif "canopy" in sid:
            height = max(height, z_top * 0.85)
        elif solid.blocks_los:
            height = max(height, z_top)
    if col.floor_ch in "T":
        height = max(height, 3.0)
    if col.floor_ch in "&@":
        height = max(height, 2.0)
    return height


def gather_shadow_casters(
    world_map,
    layer: str,
    wx0: int,
    wy0: int,
    wx_lo: int,
    wx_hi: int,
    wy_lo: int,
    wy_hi: int,
    *,
    visible: set[tuple[int, int]],
    is_explored,
    player_pos: tuple[int, int],
    companion_positions: list[tuple[int, int]],
) -> list[ShadowCaster]:
    casters: list[ShadowCaster] = []
    for wx in range(wx_lo, wx_hi + 1):
        for wy in range(wy_lo, wy_hi + 1):
            state = visibility_state(wx, wy, visible, is_explored)
            if state == UNEXPLORED:
                continue
            col = world_map.get_column(wx, wy, layer)
            h = column_caster_height(col)
            if h >= 0.75:
                strength = 1.0 if h >= 2.0 else 0.75
                casters.append(
                    ShadowCaster(wx - wx0, wy - wy0, h, strength=strength)
                )

    px, py = player_pos
    casters.append(
        ShadowCaster(
            px - wx0,
            py - wy0,
            DEFAULT_PLAYER_HEIGHT_M,
            strength=0.9,
        )
    )
    for cx, cy in companion_positions:
        casters.append(
            ShadowCaster(
                cx - wx0,
                cy - wy0,
                DEFAULT_PLAYER_HEIGHT_M * 0.95,
                strength=0.85,
            )
        )
    return casters
