"""Player movement: smooth stride + held-key repeat."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from src.audio.tile_sounds import resolve_footstep
from src.constants import INPUT_REPEAT_INITIAL_MS, INPUT_REPEAT_MS, PLAYER_MOVE_SPEED_TPS

if TYPE_CHECKING:
    from src.scenes.overworld.overworld_scene import OverworldScene
    from src.input import InputState


def _repeat_ms() -> tuple[int, int]:
    initial = int(os.environ.get("PEPELNY_INPUT_REPEAT_INITIAL_MS", str(INPUT_REPEAT_INITIAL_MS)))
    repeat = int(os.environ.get("PEPELNY_INPUT_REPEAT_MS", str(INPUT_REPEAT_MS)))
    return max(0, initial), max(16, repeat)


class LocomotionController:
    def __init__(self, scene: OverworldScene):
        self._scene = scene
        self._repeat_timer_ms = 0
        self._initial_wait_ms, self._repeat_ms = _repeat_ms()

    def reset_repeat(self) -> None:
        self._repeat_timer_ms = 0

    def update(self, inp: InputState, dt_ms: int) -> bool:
        """Advance smooth motion and try new strides. Return True if scene change requested."""
        ow = self._scene
        player = ow.player
        speed = float(os.environ.get("PEPELNY_MOVE_SPEED_TPS", str(PLAYER_MOVE_SPEED_TPS)))

        if player.update_motion(dt_ms, speed_tps=speed):
            self._on_enter_tile()

        if player.is_moving():
            return False

        d = self._movement_dir(inp)
        if d is None:
            self._repeat_timer_ms = 0
            return False

        if inp.dir_key_pressed():
            self._repeat_timer_ms = 0
            return self._finish_stride_attempt(d, dt_ms, speed)

        self._repeat_timer_ms += dt_ms
        if self._repeat_timer_ms >= self._repeat_ms:
            self._repeat_timer_ms = 0
            return self._finish_stride_attempt(d, dt_ms, speed)
        return False

    def _finish_stride_attempt(self, d: tuple[int, int], dt_ms: int, speed: float) -> bool:
        if not self._try_stride(d):
            return False
        ow = self._scene
        if getattr(ow.game, "_pending_action", None):
            return True
        if ow.player.update_motion(dt_ms, speed_tps=speed):
            self._on_enter_tile()
        return False

    def _movement_dir(self, inp: InputState) -> tuple[int, int] | None:
        from src.render.render_mode import is_iso

        if is_iso():
            if inp.nav_up_held():
                from src.render.iso_projector import IsoProjector

                return IsoProjector.screen_delta_to_world(0, -1)
            if inp.nav_down_held():
                from src.render.iso_projector import IsoProjector

                return IsoProjector.screen_delta_to_world(0, 1)
            if inp.nav_left_held():
                from src.render.iso_projector import IsoProjector

                return IsoProjector.screen_delta_to_world(-1, 0)
            if inp.nav_right_held():
                from src.render.iso_projector import IsoProjector

                return IsoProjector.screen_delta_to_world(1, 0)
            return None
        if inp.nav_up_held():
            return (0, -1)
        if inp.nav_down_held():
            return (0, 1)
        if inp.nav_left_held():
            return (-1, 0)
        if inp.nav_right_held():
            return (1, 0)
        return None

    def _try_stride(self, d: tuple[int, int]) -> bool:
        ow = self._scene
        player = ow.player
        nx, ny = player.tile_x + d[0], player.tile_y + d[1]
        layer = ow.game.world_state.layer
        wm = ow.game.world_map
        if layer == "surface":
            wm.ensure_chunk_at(nx, ny)
        if not wm.is_walkable(nx, ny, layer, ow.game.profile.body_height_m):
            return False
        ch, _, _ = wm.get_tile(nx, ny, layer)
        if ch == ">":
            ow.game.audio.play_sfx("stairs")
            ow.game.request_scene("dungeon_enter")
            return True
        if ch == "<":
            ow.game.audio.play_sfx("stairs")
            ow.game.request_scene("surface_exit")
            return True
        player.begin_stride(d[0], d[1])
        self._preload_chunks_ahead(d)
        ow.camera.reset_pan()
        if getattr(ow.game, "tutorial", None):
            ow.game.tutorial.notify_moved()
        surface = resolve_footstep(nx, ny, layer, wm)
        ow.game.audio.play_footstep(surface)
        return True

    def _preload_chunks_ahead(self, d: tuple[int, int]) -> None:
        """Stream chunks in movement direction before the player arrives."""
        if d == (0, 0):
            return
        ow = self._scene
        if ow.game.world_state.layer != "surface":
            return
        from src.constants import CHUNK_SIZE

        wm = ow.game.world_map
        lookahead = int(os.environ.get("PEPELNY_CHUNK_LOOKAHEAD", "2"))
        px, py = ow.player.tile_x, ow.player.tile_y
        for step in range(1, lookahead + 1):
            tiles = step * CHUNK_SIZE // 2
            wm.ensure_chunk_at(px + d[0] * tiles, py + d[1] * tiles)

    def _on_enter_tile(self) -> None:
        ow = self._scene
        player = ow.player
        tx, ty = player.tile_pos()
        layer = ow.game.world_state.layer
        ow.fov.mark_dirty()
        bench = os.environ.get("PEPELNY_BENCH", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        if not bench:
            ow.map_renderer.invalidate_queue_cache()
        ow.game.world_state.turn_count += 1
        active, _ = ow.weather.on_turn(ow.fov.in_shelter())
        if active and layer == "surface" and ow.log is not None:
            ow.log.add("Пепельный ветер...")
        ch, _, _ = ow.game.world_map.get_tile(tx, ty, layer)
        bid = ow.interaction.battle_for_tile(ch, tx, ty)
        if bid:
            ow.pending_battle = bid
            ow.game.world_state.defeated_battles.add((tx, ty, layer))
