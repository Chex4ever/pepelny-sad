"""Legacy T tile migration."""
from src.world.chunk import Chunk
from src.world.chunk_migration import migrate_legacy_tree_tiles


def test_migrate_t_to_tree_anchor():
    chunk = Chunk(0, 0)
    chunk.set_floor(5, 5, "T", stencil_id="tree")
    n = migrate_legacy_tree_tiles(chunk, 99)
    assert n == 1
    assert chunk.get(5, 5) == "."
    assert any(a.structure_id == "tree" for a in chunk.structure_anchors)
