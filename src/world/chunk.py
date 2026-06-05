"""Chunk tile storage."""
from __future__ import annotations

from collections import Counter

from src.constants import CHUNK_SIZE
from src.world.column import Column, Solid


class Chunk:
    def __init__(self, cx: int, cy: int):
        self.cx = cx
        self.cy = cy
        n = CHUNK_SIZE * CHUNK_SIZE
        self.tiles = ["."] * n
        self.fg = [(100, 130, 90)] * n
        self.bg = [(30, 45, 30)] * n
        self.floor_stencils = ["grass"] * n
        self.explored = [False] * n
        self.cell_solids: list[list[Solid]] = [[] for _ in range(n)]
        self.structure_anchors: list = []
        self.biome_counts: Counter = Counter()

    def idx(self, lx: int, ly: int) -> int:
        return ly * CHUNK_SIZE + lx

    def in_bounds(self, lx: int, ly: int) -> bool:
        return 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE

    def get(self, lx: int, ly: int) -> str:
        if not self.in_bounds(lx, ly):
            return "#"
        return self.tiles[self.idx(lx, ly)]

    def set_floor(self, lx: int, ly: int, ch: str, fg=None, bg=None, stencil_id: str = "grass"):
        if not self.in_bounds(lx, ly):
            return
        i = self.idx(lx, ly)
        self.tiles[i] = ch
        if fg:
            self.fg[i] = fg
        if bg:
            self.bg[i] = bg
        self.floor_stencils[i] = stencil_id

    def set(self, lx: int, ly: int, ch: str, fg=None, bg=None, *, stencil_id: str | None = None):
        if stencil_id is None:
            from src.render.tile_stencil import CHAR_STENCIL

            stencil_id = CHAR_STENCIL.get(ch, "grass")
        self.set_floor(lx, ly, ch, fg, bg, stencil_id=stencil_id)

    def add_solid(self, lx: int, ly: int, solid: Solid) -> None:
        if not self.in_bounds(lx, ly):
            return
        self.cell_solids[self.idx(lx, ly)].append(solid)

    def get_solids(self, lx: int, ly: int) -> list[Solid]:
        if not self.in_bounds(lx, ly):
            return []
        solids = self.cell_solids[self.idx(lx, ly)]
        return sorted(solids, key=lambda s: (s.z_min, s.sort_bias))

    def set_cell_solids(self, lx: int, ly: int, solids: list[Solid]) -> None:
        if not self.in_bounds(lx, ly):
            return
        self.cell_solids[self.idx(lx, ly)] = list(solids)

    def mark_explored(self, lx: int, ly: int):
        if self.in_bounds(lx, ly):
            self.explored[self.idx(lx, ly)] = True

    @property
    def dominant_biome(self) -> str:
        if not self.biome_counts:
            return "meadow"
        return self.biome_counts.most_common(1)[0][0]

    def to_column(self, lx: int, ly: int) -> Column:
        i = self.idx(lx, ly)
        floor_ch = self.tiles[i]
        floor_sid = self.floor_stencils[i]
        if floor_ch not in ".,":
            from src.render.tile_stencil import CHAR_STENCIL

            floor_sid = CHAR_STENCIL.get(floor_ch, floor_sid)
        col = Column(
            floor_ch=floor_ch,
            floor_stencil_id=floor_sid,
            fg=self.fg[i],
            bg=self.bg[i],
        )
        for s in self.get_solids(lx, ly):
            col.add_solid(s)
        return col
