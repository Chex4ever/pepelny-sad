"""World map with chunk streaming."""
from __future__ import annotations

from src.constants import CHUNK_SIZE, STREAM_RADIUS
from src.world.chunk import Chunk
from src.world.column import CLEARANCE_OPEN, Column
from src.world.landmark_placer import apply_landmarks
from src.world.surface_gen import generate_chunk
from src.world.world_fields import init_world_fields


class WorldMap:
    def __init__(self, seed: int):
        self.seed = seed
        self.perf_stats = None
        self._column_cache: dict[tuple[int, int, str], Column] | None = None
        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.dungeon_tiles: dict[tuple[int, int], dict] = {}
        self.dungeon_explored: set[tuple[int, int]] = set()
        self._landmarks_applied = False
        init_world_fields(seed)
        self._ensure_radius(0, 0)

    def _ensure_chunk(self, cx: int, cy: int) -> None:
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = generate_chunk(cx, cy, self.seed, world_map=self)

    def _ensure_radius(self, px: int, py: int):
        cx, cy = px // CHUNK_SIZE, py // CHUNK_SIZE
        for dcy in range(-STREAM_RADIUS, STREAM_RADIUS + 1):
            for dcx in range(-STREAM_RADIUS, STREAM_RADIUS + 1):
                self._ensure_chunk(cx + dcx, cy + dcy)
        if not self._landmarks_applied:
            apply_landmarks(self.chunks, self.seed)
            self._landmarks_applied = True

    def begin_frame(self) -> None:
        self._column_cache = {}

    def end_frame(self) -> None:
        self._column_cache = None

    def world_to_chunk(self, wx: int, wy: int):
        cx = wx // CHUNK_SIZE
        cy = wy // CHUNK_SIZE
        lx = wx - cx * CHUNK_SIZE
        ly = wy - cy * CHUNK_SIZE
        return cx, cy, lx, ly

    def fast_blocks_los(self, wx: int, wy: int, layer: str = "surface") -> bool:
        if layer == "dungeon":
            from src.world.visibility import blocks_los as char_blocks_los

            t = self.dungeon_tiles.get((wx, wy))
            if not t:
                return True
            return char_blocks_los(t["ch"])
        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        chunk = self.chunks.get((cx, cy))
        if not chunk or not chunk.in_bounds(lx, ly):
            return True
        if chunk.tiles[chunk.idx(lx, ly)] in "░#":
            return True
        for s in chunk.get_solids(lx, ly):
            if s.blocks_los:
                return True
        return False

    def get_column(self, wx: int, wy: int, layer: str = "surface") -> Column:
        cache_key = (wx, wy, layer)
        if self._column_cache is not None:
            cached = self._column_cache.get(cache_key)
            if cached is not None:
                if self.perf_stats is not None:
                    self.perf_stats.counter("get_column_hit")
                return cached
        if self.perf_stats is not None:
            self.perf_stats.counter("get_column")
        if layer == "dungeon":
            t = self.dungeon_tiles.get((wx, wy), {"ch": "#", "fg": (50, 50, 60), "bg": (15, 15, 20)})
            return Column(floor_ch=t["ch"], fg=t["fg"], bg=t["bg"])

        cx, cy, lx, ly = self.world_to_chunk(wx, wy)
        self._ensure_chunk(cx, cy)
        chunk = self.chunks.get((cx, cy))
        if not chunk:
            return Column(floor_ch="░", fg=(60, 60, 70), bg=(15, 15, 20))
        col = chunk.to_column(lx, ly)
        if self._column_cache is not None:
            self._column_cache[cache_key] = col
        return col

    def get_tile(self, wx: int, wy: int, layer: str = "surface") -> tuple[str, tuple, tuple]:
        col = self.get_column(wx, wy, layer)
        return col.top_display_char(), col.fg, col.bg

    def clearance_m(self, wx: int, wy: int, layer: str = "surface") -> float:
        return self.get_column(wx, wy, layer).clearance_m()

    def is_walkable(self, wx: int, wy: int, layer: str = "surface", body_height_m: float = 1.8) -> bool:
        if layer == "dungeon":
            ch, _, _ = self.get_tile(wx, wy, layer)
            return ch not in "#░"
        col = self.get_column(wx, wy, layer)
        if col.floor_ch in "░#":
            return False
        return col.clearance_m() >= body_height_m

    def blocks_los(self, wx: int, wy: int, layer: str = "surface") -> bool:
        return self.fast_blocks_los(wx, wy, layer)

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
