# Render engine (`src/engine/`)

Unified tile-map → screen pipeline for editors and (future) game migration.

## Layers

| Package | Role |
|---------|------|
| `engine/layout/` | Diag stamp lattice, golden 1 m reference, `TILE_SLOT_VIEW` |
| `engine/projection/` | **Tile → screen:** `char_cell_to_iso`, `layout_cell_to_screen`, `world_to_screen` |
| `engine/floor/` | Packed floor patch: `build_floor_patch`, `floor_packed_draw_map` (1 m diamond) |
| `engine/world/` | `build_surface_draw_queue` — Chunk columns → WYSIWYG draw queue |
| `engine/viewport/` | Bounds, `draw_packed_floor`, blit helpers |
| `engine/api.py` | `EngineViewport`, `RenderScene`, `WorldScene`, `FloorScene` |

## Two projection modes

1. **Packed layout (character editor floor)** — axis-aligned screen grid; stamp slots per `docs/ISO_LAYOUT.md` (axis silhouettes for `tx`/`ty`); not iso-skewed.
2. **World iso (overworld game — legacy)** — `IsoProjector` + draw queue; level editor **no longer** uses this for floor view.

## Public API (minimum)

```python
from src.engine import EngineViewport, WorldScene
from src.engine.projection import char_cell_to_iso, layout_cell_to_screen, world_to_screen
from src.engine.floor import floor_packed_draw_map, build_floor_patch
```

## Clients

| Script | Engine usage |
|--------|----------------|
| `scripts/character_editor.py` | `engine/floor` + packed viewport (via `IsoCharacterRenderer`) |
| `scripts/level_editor.py` | `engine/floor` packed diag viewport + `EditableWorld` |
| `scripts/biome_viewer.py` | Same queue as `engine/world` (direct `OverworldPreview` today) |

## Floor sizing

- `EDITOR_FLOOR_TILES` / `FLOOR_LAYOUT_TILES` = 5 (one 1 m layout unit).
- `editor_floor_patch_tiles()` = level-editor patch side (default 5 m → 25 tiles).

Character editor uses **1 m** only. Larger single-diamond layouts are a separate `engine/floor/` task.

## Layout resolution

| Patch size | Slot positions |
|------------|----------------|
| 5×5 (1 m) | Golden canvas `EDITOR_FLOOR_5X5_TILE_REFERENCE` → `resolve_tile_slot_view` |
| n×n (level editor) | `screen_row_tile_slot` + `build_tile_slot_screen_map` (cached per `n`) |

See `src/engine/layout/golden.py`, `src/engine/layout/screen_slots.py`.

## Tests

- `tests/unit/test_engine_projection.py` — projection + golden draw map
- `tests/unit/test_editor_floor_iso.py` — packed diamond regression
- `tests/unit/test_editor_document.py` — map JSON round-trip
- `tests/unit/test_alphabet_floor_render.py` — 5×5 alphabet golden on 19×10 canvas
- `tests/unit/test_screen_slot_layout.py` — screen-row stamp layout
- `tests/regression/test_level_editor_startup.py` — level editor smoke frame

## Performance

- Overworld GPU: [`PERFORMANCE.md`](PERFORMANCE.md)
- Level editor CPU: [`LEVEL_EDITOR_PERFORMANCE.md`](LEVEL_EDITOR_PERFORMANCE.md)

## Legacy re-exports

`src/characters/editor_floor.py` and `editor_floor_test_tiles.py` re-export engine modules; prefer `src.engine.*` in new code.
