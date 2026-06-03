"""World map with chunk streaming."""
from __future__ import annotations

from src.constants import CHUNK_SIZE, STREAM_RADIUS
from src.world.chunk import Chunk
from src.world.landmark_placer import apply_landmarks
from src.world.surface_gen import generate_chunk


class WorldMap:
    def __init__(self, seed: int):
        self.seed = seed
        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.dungeon_tiles: dict[tuple[int, int], dict] = {}
        self.dungeon_explored: set[tuple[int, int]] = set()
        self._landmarks_applied = False
        self._ensure_radius(0, 0)

    def _ensure_radius(self, px: int, py: int):
        cx, cy = px // CHUNK_SIZE, py // CHUNK_SIZE
        for dcy in range(-STREAM_RADIUS, STREAM_RADIUS + 1):
            for dcx in range(-STREAM_RADIUS, STREAM_RADIUS + 1):
                key = (cx + dcx, cy + dcy)
                if key not in self.chunks:
                    self.chunks[key] = generate_chunk(key[0], key[1], self.seed)
        if not self._landmarks_applied:
            apply_landmarks(self.chunks, self.seed)
            self._landmarks_applied = True

    def world_to_chunk(self, wx: int, wy: int):
        cx = wx // CHUNK_SIZE
        cy = wy // CHUNK_SIZE
        lx = wx - cx * CHUNK_SIZE
        ly = wy - cy * CHUNK_SIZE
        return cx, cy, lx, ly

    def get_tile(self, wx: int, wy: int, layer: str = "surface") -> tuple[str, tuple, tuple]:
        if layer == "dungeon":
            key = (wx, wy)
            if key in self.dungeon_tiles:
                t = self.dungeon_tiles[key]
                return t["ch"], t["fg"], t["bg"]
            return "#", (50, 50, 60), (15, 15, 20)

        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        self._ensure_radius(wx, wy)
        chunk = self.chunks.get((cx, cy))
        if not chunk:
            return "░", (60, 60, 70), (15, 15, 20)
        i = chunk.idx(lx, ly)
        return chunk.tiles[i], chunk.fg[i], chunk.bg[i]

    def is_walkable(self, wx: int, wy: int, layer: str = "surface") -> bool:
        ch, _, _ = self.get_tile(wx, wy, layer)
        return ch not in "#T░"

    def set_dungeon_tile(self, wx: int, wy: int, ch: str, fg=(120, 120, 140), bg=(20, 20, 28)):
        self.dungeon_tiles[(wx, wy)] = {"ch": ch, "fg": fg, "bg": bg}

    def is_explored(self, wx: int, wy: int, layer: str = "surface") -> bool:
        if layer == "dungeon":
            return (wx, wy) in self.dungeon_explored
        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        chunk = self.chunks.get((cx, cy))
        if not chunk or not chunk.in_bounds(lx, ly):
            return False
        return chunk.explored[chunk.idx(lx, ly)]

    def mark_explored(self, wx: int, wy: int, layer: str = "surface"):
        if layer == "dungeon":
            self.dungeon_explored.add((wx, wy))
            return
        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        chunk = self.chunks.get((cx, cy))
        if chunk:
            chunk.mark_explored(lx, ly)
