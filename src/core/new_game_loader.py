"""Build new-game state step-by-step (one step per frame)."""
from __future__ import annotations

import os
import random
from collections.abc import Generator
from typing import TYPE_CHECKING

from src.constants import CHUNK_SIZE, STREAM_RADIUS
from src.i18n import t
from src.progression.player_profile import PlayerProfile
from src.scenes.overworld.overworld_scene import OverworldScene
from src.world.landmark_placer import apply_landmarks
from src.world.surface_gen import generate_chunk
from src.world.world_fields import init_world_fields
from src.world.world_map import WorldMap
from src.world.world_state import WorldState

if TYPE_CHECKING:
    from src.game import Game

Step = tuple[str, float | None]


def iter_build_new_game(game: Game, seed: int | None = None) -> Generator[Step, None, None]:
    """Yield (status message, progress 0..1) then leave game fully initialized."""
    actual_seed = seed if seed is not None else random.randint(1, 99999)

    yield t("loading.profile"), 0.05
    game.world_state = WorldState(world_seed=actual_seed)
    game.world_state.tutorial_step = 0
    game.profile = PlayerProfile()
    game.profile.inventory.add("grey_herb", 3, 20)
    game.profile.inventory.add("root_fiber", 2, 20)

    yield t("loading.terrain"), 0.2
    game.world_map = WorldMap.__new__(WorldMap)
    game.world_map.seed = actual_seed
    game.world_map.perf_stats = game.perf
    game.world_map._column_cache = None
    game.world_map.chunks = {}
    game.world_map.dungeon_tiles = {}
    game.world_map.dungeon_explored = set()
    game.world_map._landmarks_applied = False
    game.world_map._chunk_gen_queue = []
    game.world_map._chunks_per_frame = max(
        1, int(os.environ.get("PEPELNY_CHUNKS_PER_FRAME", "2"))
    )
    game.world_map._init_streaming_state()
    init_world_fields(actual_seed)

    cx, cy = 0 // CHUNK_SIZE, 0 // CHUNK_SIZE
    coords = [
        (cx + dcx, cy + dcy)
        for dcy in range(-STREAM_RADIUS, STREAM_RADIUS + 1)
        for dcx in range(-STREAM_RADIUS, STREAM_RADIUS + 1)
    ]
    from src.core.parallel_load import chunk_worker_count

    missing = [c for c in coords if c not in game.world_map.chunks]
    workers_env = os.environ.get("PEPELNY_CHUNK_WORKERS", "").strip()
    if workers_env in ("0", "1"):
        use_parallel = False
    else:
        use_parallel = chunk_worker_count() > 1 and len(missing) > 3
    if use_parallel and len(missing) > 3:
        from src.core.parallel_load import generate_chunks_parallel

        generated = generate_chunks_parallel(missing, actual_seed)
        for key, chunk in generated.items():
            game.world_map.chunks[key] = chunk
        game.world_map.bake_all_tree_solids()
        yield t("loading.chunks"), 0.8
    else:
        total = max(1, len(missing))
        for i, (ccx, ccy) in enumerate(missing):
            key = (ccx, ccy)
            game.world_map.chunks[key] = generate_chunk(
                ccx, ccy, actual_seed, world_map=game.world_map
            )
            frac = 0.25 + 0.55 * ((i + 1) / total)
            yield t("loading.chunks"), frac

    yield t("loading.landmarks"), 0.88
    if not game.world_map._landmarks_applied:
        apply_landmarks(game.world_map.chunks, actual_seed)
        game.world_map._landmarks_applied = True

    yield t("loading.overworld"), 0.95
    game.overworld = OverworldScene(game)

    yield t("loading.done"), 1.0


def build_new_game(game: Game, seed: int | None = None) -> None:
    """Run full build synchronously (tests / direct call)."""
    for _msg, _prog in iter_build_new_game(game, seed):
        pass
