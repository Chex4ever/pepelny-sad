"""Overworld sync: FOV before draw, chunk streaming after present."""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.scenes.overworld.overworld_scene import OverworldScene


def sync_budget_ms() -> float:
    raw = os.environ.get("PEPELNY_SYNC_BUDGET_MS", "2").strip()
    if not raw:
        return 2.0
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def _over_budget(t0: float, budget_ms: float) -> bool:
    return budget_ms > 0 and (time.perf_counter() - t0) * 1000.0 >= budget_ms


def sync_for_draw(scene: OverworldScene) -> None:
    """FOV + player chunk must match current frame before map draw."""
    ow = scene
    perf = ow.game.perf
    wm = ow.game.world_map
    px, py = ow.player.tile_pos()
    from src.constants import CHUNK_SIZE

    player_chunk = (px // CHUNK_SIZE, py // CHUNK_SIZE)
    wm._ensure_chunk(player_chunk[0], player_chunk[1])

    wx0, wy0 = ow.camera.view_origin()
    if ow.fov.needs_recompute() or not ow.visible:
        with perf.measure("fov"):
            ow.visible = ow.fov.update(wx0, wy0)
    else:
        ow.visible = ow.fov.last_visible or ow.visible


def update_deferred(scene: OverworldScene, dt_ms: int) -> None:
    """Heavy work after present: chunk streaming, ambient."""
    _ = dt_ms
    ow = scene
    perf = ow.game.perf
    budget = sync_budget_ms()
    t0 = time.perf_counter()

    with perf.measure("ow_deferred"):
        wm = ow.game.world_map
        px, py = ow.player.tile_pos()

        if not _over_budget(t0, budget):
            with perf.measure("chunks_stream"):
                wm._ensure_radius(px, py)

        if not _over_budget(t0, budget):
            ow.fov.update_ambient(ow.visible)

    elapsed = (time.perf_counter() - t0) * 1000.0
    perf._timers["deferred_ms"] = elapsed
