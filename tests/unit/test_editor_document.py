"""EditorDocument JSON round-trip."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.constants import CHUNK_SIZE
from src.world.chunk import Chunk
from src.world.column import Solid
from src.world.editor.document import EditorDocument, MapBounds, load_map, save_map
from src.world.structures import StructureAnchor


@pytest.mark.unit
def test_editor_document_round_trip(tmp_path: Path):
    doc = EditorDocument(seed=99, bounds=MapBounds(wx0=10, wy0=20, width=16, height=16))
    chunk = doc.chunk_at(0, 0)
    chunk.set(3, 4, "+", stencil_id="grass_dense")
    chunk.add_solid(3, 4, Solid(0.0, 1.0, stencil_id="bush_low"))
    chunk.structure_anchors.append(StructureAnchor("bush_low", 13, 24))

    path = tmp_path / "test_map.json"
    save_map(path, doc)
    loaded = load_map(path)

    assert loaded.seed == 99
    assert loaded.bounds.width == 16
    c2 = loaded.chunk_at(0, 0)
    assert c2.get(3, 4) == "+"
    assert len(c2.get_solids(3, 4)) == 1
    assert loaded.chunks[(0, 0)].structure_anchors[0].structure_id == "bush_low"


@pytest.mark.unit
def test_editor_document_to_dict_from_dict():
    doc = EditorDocument()
    chunk = Chunk(1, 2)
    chunk.set(0, 0, ".", stencil_id="meadow")
    doc.chunks[(1, 2)] = chunk
    data = doc.to_dict()
    assert data["version"] == 1
    restored = EditorDocument.from_dict(data)
    assert (1, 2) in restored.chunks
    assert restored.chunks[(1, 2)].floor_stencils[0] == "meadow"


@pytest.mark.unit
def test_editable_world_scene_chunks():
    from src.world.editor.editable_world import EditableWorld

    side = CHUNK_SIZE + 4
    world = EditableWorld(width=side, height=side, wx0=0, wy0=0)
    world.fill_blank_grass()
    chunks = world.world_scene_chunks()
    assert len(chunks) >= 2
