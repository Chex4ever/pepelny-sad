# Iso layout (single diag scheme)

One floor layout everywhere: **3×2 char stamps** `@@_/_@@` on a diagonal tile lattice.

## World axes

| Axis | Direction in world | Facing key |
|------|-------------------|------------|
| **+X** | east | `e` → `(1, 0)` |
| **+Y** | south | `s` → `(0, 1)` |
| **−Y** | north | `n` → `(0, −1)` |
| **+Z** | up (metres) | height |

Screen (pygame): **sx right**, **sy down**.

## Stamp (one floor tile)

```
@@_   ← 3 columns, 2 rows in char cells
_@@
```

Four `@` cells per tile. Scale: **5×5 tiles = 1 m × 1 m** (`TILES_PER_M_XY=5`).

## What you see in `character_editor` — packed layout diamond

**This is what the user golden describes.** The editor draws the floor on a **19×10 packed layout grid** — the same grid as `EDITOR_FLOOR_5X5_TILE_REFERENCE`:

```
____uu_____________     row width 2
___ppuuvv__________     row width 6
...
aaffggllmmrrssxxyy_     row width 18  ← widest
...
_____________ee____     row width 2
```

Letters `a`…`y` = tile `(tx, ty)` row-major (`a` = (0,0), four identical glyphs per stamp). Row widths: `(2, 6, 10, 14, 18, 18, 14, 10, 6, 2)` — a **diamond**, flat top/bottom parallel to screen X.

## Reference sketch (5×5 tiles)

The **5×5 / 19×10** golden in `character_editor` is a **reference example** of how individual tiles interleave on the diag diamond — not a unit to copy and paste. Level editor places **each tile's stamp slots separately** on one continuous diamond for the whole patch (`compute_tile_slot_view_patch`).

## World axes (floor / level editor)

| Axis | On screen (pygame: sx→, sy↓) |
|------|------------------------------|
| **+X** | down-right |
| **+Y** | up-right |

`+Y` here is **north** on the diag lattice (opposite tessellation `ty` index in the golden sketch).

### Axis silhouettes on the packed screen

Each screen cell holds **one stamp slot** (one `@`). Digits below are **tile coordinates** on that axis (`tx` or `ty`); `_` is an empty screen cell.

**+Y (north)** — digit = `ty`. Higher `ty` toward the **top** of the sketch (smaller screen row):

```
____44
___3344
__2233
_1122
0011
_00
```

**+X (east)** — digit = `tx`. Higher `tx` toward the **bottom-right** (larger screen row and column):

```
00
_0011
____1122
_______2233
__________3344
_____________44
```

These are **reference silhouettes** for how one coordinate axis reads on screen. A real patch is the union of both axes plus the 3×2 stamp per tile (`12_` / `_34`); do not copy these blocks as metre units.

Larger patches: same rule — `screen_row_tile_slot(sr, sc)` in `src/engine/layout/screen_slots.py` (4-row cycle, then each tile's four slots form one stamp via `build_tile_slot_screen_map()`). One glyph per stamp slot; no metre-block copy.

| Property | Value |
|----------|--------|
| Layout API | `screen_row_tile_slot()`, `build_tile_slot_screen_map()`, `resolve_tile_slot_view()` |
| 5×5 positions | Decoded from `EDITOR_FLOOR_5X5_TILE_REFERENCE` (golden canvas) |
| n>5 positions | Screen-row stamps; `_STAMP_LAYOUT_CACHE` caches per `n_tiles` |
| Draw API | `floor_packed_draw_map_from_cells()` → `(col, row)` per slot |
| Camera | `cam_tx`, `cam_ty` — anchor tile slot **0** at packed origin (n>5 only) |
| Screen offset | `layout_cell_to_screen(col, row)` — axis-aligned pygame grid |

**Not** iso-skewed `floor_screen_offset` (that is a rectangle, not this diamond).

### Layout rules

1. Screen row 0 example: `(0,0,1),(0,0,2),(0,1,3),(0,1,4),(1,1,1)...` — slots 1–2 on `(i,i)`, slots 3–4 on `(i,i+1)`.
2. 25 tiles → 100 screen cells (4 per tile); seam char cells may repeat the same grass glyph.
3. Test letters (`a`…`y`) label slots in `TILE_SLOT_DISPLAY`; game uses grass/checkerboard.

## 2:1 iso projection (overworld / voxels only)

Used for **character voxels** (`IsoProjector`, `_project_point`) and **overworld** — **not** for editor floor placement:

```
su = (dx − dy) × 2
sv = (dx + dy) × 1
```

| Step in world | On screen |
|---------------|-----------|
| +X | down-right |
| +Y (south) | down-left |
| −Y (north) | up-right |

See `IsoProjector.screen_delta_to_world` for walk directions.

## Orientation test — 2×2 patch

Separate golden: `EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE` (16 single-char slots).

## Tessellation vs walk

| | Neighbors | Coords |
|---|-----------|--------|
| Floor tessellation | 6 | `(tx, ty)` |
| Overworld walk | 4 screen steps | `(wx, wy)` |

## Code map

| Module | Role |
|--------|------|
| `src/engine/layout/golden.py` | Golden 5×5, `resolve_tile_slot_view`, alphabet test helpers |
| `src/engine/layout/screen_slots.py` | Screen-row rule, stamp layout cache, pick map |
| `src/engine/floor/` | `floor_packed_draw_map_from_cells()`, world patch |
| `src/engine/projection/` | `char_cell_to_iso`, `layout_cell_to_screen`, `world_to_screen` |
| `src/world/editor/ui/viewport.py` | Level editor `draw_diag_viewport` |
| `src/characters/editor_floor.py` | Legacy re-export of engine floor |
| `iso_character_renderer.py` | Character editor packed floor draw |
| `test_alphabet_floor_render.py` | 5×5 letter golden regression |
| `test_editor_floor_iso.py` | Diamond silhouette + “iso ≠ editor shape” regression |

See also `docs/ENGINE.md`, `docs/LEVEL_EDITOR.md`, `docs/LEVEL_EDITOR_PERFORMANCE.md`.
