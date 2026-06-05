"""Overworld frame order: input/move before FOV recompute."""
from __future__ import annotations

from unittest.mock import patch

import pygame

from tests.conftest import FakeInput


def _complete_stride_dt() -> int:
    """Enough ms to finish one smooth stride at default speed in tests."""
    return 250


def test_move_before_fov_los_in_game_frame_order(game):
    ow = game.overworld
    px_before = ow.player.tile_x
    fov_calls: list[tuple[int, int]] = []

    orig = ow.fov.update

    def tracking_update(wx0, wy0):
        fov_calls.append(ow.player.tile_pos())
        return orig(wx0, wy0)

    ow.fov.update = tracking_update  # type: ignore[method-assign]

    from src.core.perf_benchmark import run_overworld_frame

    run_overworld_frame(
        game, FakeInput(pressed={pygame.K_d}), dt_ms=_complete_stride_dt()
    )

    assert ow.player.tile_x != px_before
    assert len(fov_calls) >= 1
    assert fov_calls[0] == ow.player.tile_pos()


def test_fov_runs_in_prepare_draw_before_deferred(game):
    """FOV must update in prepare_draw so draw sees tiles at the new player position."""
    ow = game.overworld
    start_x = ow.player.tile_x
    los_calls: list[tuple[int, int]] = []

    with patch("src.scenes.overworld.fov_controller.cast_los_fov") as mock_los:
        def capture(px, py, radius, blocks_fn):
            los_calls.append((px, py))
            return {(px, py), (px + 1, py)}

        mock_los.side_effect = capture

        ow.handle_input(FakeInput(pressed={pygame.K_d}), dt_ms=_complete_stride_dt())
        assert ow.player.tile_x != start_x
        assert len(los_calls) == 0

        ow.prepare_draw()
        assert len(los_calls) >= 1
        assert los_calls[-1] == ow.player.tile_pos()
        assert ow.player.tile_pos() in ow.visible

        ow.update_deferred()
