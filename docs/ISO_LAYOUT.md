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
____kk_____________     row width 2
___ggkkpp__________     row width 6
...
aabbeehhmmqquuwwyy_     row width 18  ← widest
...
_____________oo____     row width 2
```

Row widths: `(2, 6, 10, 14, 18, 18, 14, 10, 6, 2)` — a **diamond**, flat top/bottom parallel to screen X.

| Property | Value |
|----------|--------|
| Canvas | 19 cols × 10 rows |
| Draw API | `floor_packed_draw_map()` + `TILE_SLOT_VIEW` |
| Feet anchor | `(PACKED_LAYOUT_FEET_COL, PACKED_LAYOUT_FEET_ROW)` = `(9, 5)` |
| Screen offset | `(col − 9, row − 5)` — **axis-aligned**, not iso-skewed |
| Test | `test_editor_floor_draw_matches_golden_diamond_silhouette` |

**Not** the same as projecting tessellation char cells through `floor_screen_offset` (iso skew) — that yields a **rectangle / staircase**, not this diamond.

### Layout golden rules

1. 25 tiles → 25 letters in the test sketch (`a`…`y`), each **4 times** (100 glyph cells).
2. `aa` on one row = two adjacent `@` of the same tile (pair columns in the sketch).
3. In game: grass/checkerboard on the same cells; letters are test labels only.

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
| `editor_floor_test_tiles.py` | `TILE_SLOT_VIEW`, layout golden, `packed_layout_silhouette()` |
| `editor_floor.py` | `floor_packed_draw_map()` |
| `iso_character_renderer.py` | Draws packed `(col, row)` grid |
| `test_editor_floor_iso.py` | Diamond silhouette + “iso ≠ editor shape” regression |
