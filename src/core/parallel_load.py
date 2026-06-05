"""Optional multiprocessing for chunk generation (bypasses GIL on load)."""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.world.chunk import Chunk

_worker_seed: int | None = None


def _project_root() -> str:
    from pathlib import Path

    return str(Path(__file__).resolve().parents[2])


def _init_worker(seed: int, base_path: str) -> None:
    global _worker_seed
    _worker_seed = seed
    from src.constants import init_paths
    from src.world.world_fields import init_world_fields

    init_paths(base_path)
    init_world_fields(seed)


def _generate_chunk_worker(coord: tuple[int, int]) -> tuple[tuple[int, int], Chunk]:
    from src.world.surface_gen import generate_chunk_isolated

    cx, cy = coord
    assert _worker_seed is not None
    chunk = generate_chunk_isolated(cx, cy, _worker_seed)
    return (cx, cy), chunk


def chunk_worker_count() -> int:
    raw = os.environ.get("PEPELNY_CHUNK_WORKERS", "").strip()
    if raw:
        try:
            return max(1, min(16, int(raw)))
        except ValueError:
            pass
    n = os.cpu_count() or 4
    return max(1, min(4, n - 1))


def generate_chunks_parallel(
    coords: list[tuple[int, int]],
    seed: int,
) -> dict[tuple[int, int], Chunk]:
    """Generate many chunks in worker processes; caller merges trees on main thread."""
    if len(coords) <= 1:
        from src.world.surface_gen import generate_chunk_isolated

        cx, cy = coords[0]
        return {(cx, cy): generate_chunk_isolated(cx, cy, seed)}

    workers = min(chunk_worker_count(), len(coords))
    out: dict[tuple[int, int], Chunk] = {}
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_worker,
        initargs=(seed, _project_root()),
    ) as pool:
        futures = [pool.submit(_generate_chunk_worker, c) for c in coords]
        for fut in as_completed(futures):
            key, chunk = fut.result()
            out[key] = chunk
    return out
