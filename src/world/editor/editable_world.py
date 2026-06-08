"""Editable world patch for level editor."""
from __future__ import annotations

from src.constants import CHUNK_SIZE
from src.engine.config import editor_floor_patch_tiles
from src.world.chunk import Chunk
from src.world.editor.document import EditorDocument, MapBounds


class EditableWorld:
    """In-memory surface map centered on a configurable patch."""

    def __init__(
        self,
        *,
        seed: int = 0,
        width: int | None = None,
        height: int | None = None,
        wx0: int = 0,
        wy0: int = 0,
    ) -> None:
        side = width if width is not None else editor_floor_patch_tiles()
        h = height if height is not None else side
        self.doc = EditorDocument(
            seed=seed,
            bounds=MapBounds(wx0=wx0, wy0=wy0, width=side, height=h),
        )
        self._focus_wx = wx0 + side // 2
        self._focus_wy = wy0 + h // 2

    @property
    def seed(self) -> int:
        return self.doc.seed

    @property
    def bounds(self) -> MapBounds:
        return self.doc.bounds

    def focus(self) -> tuple[int, int]:
        return self._focus_wx, self._focus_wy

    def pan_focus(self, dx: int, dy: int) -> None:
        b = self.bounds
        self._focus_wx = max(b.wx0, min(b.wx0 + b.width - 1, self._focus_wx + dx))
        self._focus_wy = max(b.wy0, min(b.wy0 + b.height - 1, self._focus_wy + dy))

    def fill_blank_grass(self) -> None:
        """Initialize all cells in bounds to default grass."""
        for wx, wy in self.iter_local_cells():
            chunk, lx, ly = self.chunk_for_world(wx, wy)
            chunk.set(lx, ly, ".", stencil_id="grass")

    def iter_local_cells(self):
        b = self.bounds
        for dy in range(b.height):
            for dx in range(b.width):
                yield b.wx0 + dx, b.wy0 + dy

    def chunk_for_world(self, wx: int, wy: int) -> tuple[Chunk, int, int]:
        cx, cy, lx, ly = self.doc.world_to_chunk(wx, wy)
        return self.doc.chunk_at(cx, cy), lx, ly

    def world_scene_chunks(self) -> list[tuple[Chunk, int, int, int, int]]:
        """Chunks overlapping bounds as (chunk, wx0, wy0, w, h) local slices."""
        b = self.doc.bounds
        cx0 = b.wx0 // CHUNK_SIZE
        cy0 = b.wy0 // CHUNK_SIZE
        cx1 = (b.wx0 + b.width - 1) // CHUNK_SIZE
        cy1 = (b.wy0 + b.height - 1) // CHUNK_SIZE
        out: list[tuple[Chunk, int, int, int, int]] = []
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                chunk = self.doc.chunk_at(cx, cy)
                wx0 = max(b.wx0, cx * CHUNK_SIZE)
                wy0 = max(b.wy0, cy * CHUNK_SIZE)
                wx1 = min(b.wx0 + b.width, (cx + 1) * CHUNK_SIZE)
                wy1 = min(b.wy0 + b.height, (cy + 1) * CHUNK_SIZE)
                out.append((chunk, wx0, wy0, wx1 - wx0, wy1 - wy0))
        return out
