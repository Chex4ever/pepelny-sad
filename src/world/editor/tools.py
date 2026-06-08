"""Level editor paint/place tools."""
from __future__ import annotations

import random

from src.data.art_loader import load_biomes
from src.world.editor.editable_world import EditableWorld
from src.world.structures import StructureAnchor, _solids_from_template
from src.world.tree_generator import build_tree_solids, tree_anchor


class EditorTools:
    def __init__(self, world: EditableWorld) -> None:
        self.world = world
        self.active_stencil = "grass"
        self.active_char = "."
        self.active_structure = "bush_low"

    def paint_floor(
        self,
        wx: int,
        wy: int,
        *,
        ch: str | None = None,
        stencil_id: str | None = None,
    ) -> None:
        chunk, lx, ly = self.world.chunk_for_world(wx, wy)
        chunk.set(lx, ly, ch or self.active_char, stencil_id=stencil_id or self.active_stencil)

    def erase_cell(self, wx: int, wy: int) -> None:
        chunk, lx, ly = self.world.chunk_for_world(wx, wy)
        chunk.set(lx, ly, ".", stencil_id="grass")
        chunk.set_cell_solids(lx, ly, [])
        chunk.structure_anchors = [
            a for a in chunk.structure_anchors if not (a.wx == wx and a.wy == wy)
        ]

    def place_structure_at(self, wx: int, wy: int, structure_id: str | None = None) -> None:
        sid = structure_id or self.active_structure
        chunk, _lx, _ly = self.world.chunk_for_world(wx, wy)
        chunk.structure_anchors.append(StructureAnchor(sid, wx, wy))
        for dx, dy, solid in _solids_from_template(sid):
            c2, lx2, ly2 = self.world.chunk_for_world(wx + dx, wy + dy)
            c2.add_solid(lx2, ly2, solid)

    def place_tree(self, wx: int, wy: int, *, biome_id: str = "meadow") -> None:
        biomes = load_biomes()
        biome = biomes.get(biome_id, biomes.get("meadow", {}))
        chunk, _lx, _ly = self.world.chunk_for_world(wx, wy)
        anchor = tree_anchor(wx, wy, biome, self.world.seed)
        chunk.structure_anchors.append(anchor)
        if anchor.params:
            for dx, dy, solid in build_tree_solids(anchor.params):
                c2, lx2, ly2 = self.world.chunk_for_world(wx + dx, wy + dy)
                c2.add_solid(lx2, ly2, solid)

    def scatter_bushes(
        self,
        wx0: int,
        wy0: int,
        w: int,
        h: int,
        *,
        density: float = 0.08,
        structure_id: str = "bush_low",
    ) -> None:
        rng = random.Random(self.world.seed ^ 0xB00E)
        for dy in range(h):
            for dx in range(w):
                if rng.random() >= density:
                    continue
                self.place_structure_at(wx0 + dx, wy0 + dy, structure_id)
