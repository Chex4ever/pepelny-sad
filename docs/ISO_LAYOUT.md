# Iso layout (single diag scheme)

One floor layout everywhere: **3×2 char stamps** `@@_/_@@` on a diagonal tile lattice.

## World axes

| Axis | Direction in world | Facing key |
|------|-------------------|------------|
| **+X** | east | `e` → `(1, 0)` |
| **+Y** | south | `s` → `(0, 1)` |
| **−Y** | north | `n` → `(0, −1)` |
| **+Z** | up (metres) | height |

Screen (pygame): **sx right**, **sy down**. Z up → sy decreases.

## Stamp (one floor tile)

```
@@_   ← 3 columns, 2 rows in char cells
_@@
```

Four `@` cells = four glyph positions. **One tile → one test letter → 4 copies** on the layout golden.

- **Stamp:** `STAMP_PREVIEW = ("@@_/_@@", "_@@")`
- **Tip:** `stamp_tip(tx, ty) = (tx − ty, tx + ty)` in tessellation char space
- **Origin:** `stamp_origin(tx, ty) = tip − (1, 1)`
- **Neighbors:** six shared-edge tiles via `tile_neighbors()` on `(tx, ty)`

## Scale

| Axis | Tiles per meter |
|------|-----------------|
| XY   | 5 (`TILES_PER_M_XY`) |
| Z    | 10 (`TILES_PER_M_Z`) |

Editor floor: **5×5 tiles** = **1 m × 1 m** patch centered on the character feet.

## Screen projection (2:1 steps)

Separate from stamp **3×2** shape. Used when drawing char coords on screen:

```
su = (cx − ref_x − (cy − ref_y)) × ISO_STEP_X    # ISO_STEP_X = 2
sv = (cx − ref_x + (cy − ref_y)) × ISO_STEP_Y    # ISO_STEP_Y = 1
```

One world/char step effects on screen (same as `IsoProjector`):

| Step `(dx, dy)` | Δsu | Δsv | On screen |
|-----------------|-----|-----|-----------|
| **+X** `(1, 0)` | +2 | +1 | down-right |
| **+Y** `(0, 1)` south | −2 | +1 | down-left |
| **−Y** `(0, −1)` north | +2 | −1 | up-right |
| **−X** `(-1, 0)` | −2 | −1 | up-left |

```
              −Y (north)
                 ↗
                /
    −X ←-------●------→ +X
                \
                 ↘
              +Y (south)
```

**2:1** = horizontal screen step is **twice** the vertical step along these axes (`ISO_STEP_X : ISO_STEP_Y = 2 : 1`).

## Two tests — do not confuse them

| Test | What it checks | Golden |
|------|----------------|--------|
| **Layout packed** | Stamp `@` positions packed to ASCII (labels only) | `EDITOR_FLOOR_5X5_TILE_REFERENCE` (19×10, 25×4 letters) |
| **Editor iso screen** | What `character_editor` draws: span-filled iso cells, **no row gaps** | `assert_floor_has_no_holes()` + `floor_iso_draw_map()` |

The layout golden is **not** a screenshot of grass. The editor test verifies **continuous floor** on iso screen (row spans filled between projected `@` cells).

### Layout golden rules

1. 25 tiles → 25 letters (`a`…`y`), each **4 times** (100 chars).
2. `aa` on one row = two `@` of the **same** tile side by side.
3. `_` = padding; no row gaps inside the diamond.

Example:

```
____kk_____________
___ggkkpp__________
aabbeehhmmqquuwwyy_
```

## Orientation test — 2×2 patch

All **16** `@` slots, one letter each. Golden: `EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE`. Separate rules from 5×5.

## Walking vs tessellation

| | Directions | Coordinates |
|---|------------|-------------|
| **Tessellation** | 6 neighbors | `(tx, ty)` |
| **Overworld walk** | 4 screen steps (↑↓←→) | `(wx, wy)` via `IsoProjector.screen_delta_to_world` |

## Code map

| Module | Role |
|--------|------|
| `editor_floor.py` | Stamp patch, iso draw map, hole checks |
| `editor_floor_test_tiles.py` | Layout golden + `render_packed_test_floor()` |
| `iso_character_renderer.py` | Draws `floor_iso_draw_map()` in editor |
| `tests/unit/test_editor_floor_iso.py` | Iso screen + packed golden |
| `tests/unit/test_editor_floor_tile_reference.py` | Layout golden char-by-char |
