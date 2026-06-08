"""Per-tile packed layout: no metre-block seams on the patch."""
from __future__ import annotations

import pytest


@pytest.mark.unit
def test_tile_steps_are_uniform_across_patch_not_metre_boundaries():
    """Steps between neighbours must not jump at every 5 tiles (no 5×5 copy grid)."""
    from src.engine.config import FLOOR_LAYOUT_TILES
    from src.engine.projection.packed import layout_cell_to_screen
    from src.world.editor.editable_world import EditableWorld
    from src.world.editor.ui.viewport import build_world_packed_draw_map

    n = FLOOR_LAYOUT_TILES * 3  # 15×15
    world = EditableWorld(seed=2, width=n, height=n)
    world.fill_blank_grass()
    draw_map, _wx0, _wy0, _side = build_world_packed_draw_map(world)

    def tile_screen(tx: int, ty: int) -> tuple[int, int] | None:
        cells = [
            (col, row)
            for (col, row), c in draw_map.items()
            if c.tile_tx == tx and c.tile_ty == ty
        ]
        if not cells:
            return None
        return layout_cell_to_screen(*cells[0])

    ty = 7
    steps: list[tuple[int, int]] = []
    for tx in range(2, n - 2):
        a = tile_screen(tx, ty)
        b = tile_screen(tx + 1, ty)
        if a and b:
            steps.append((b[0] - a[0], b[1] - a[1]))

    assert len(steps) >= 8
    unit = FLOOR_LAYOUT_TILES
    for i, (dx, dy) in enumerate(steps):
        if i + 1 >= len(steps):
            break
        ndx, ndy = steps[i + 1]
        # Seam at metre boundary would show as a spike only there.
        if (i + 1) % unit == 0:
            assert abs(ndx - dx) <= 8 and abs(ndy - dy) <= 8, (
                f"jump at metre boundary after tile {i + 1}: {steps[i]} -> {steps[i + 1]}"
            )
