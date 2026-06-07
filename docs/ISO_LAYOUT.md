# Iso layout (single diag scheme)

One floor layout everywhere: **3×2 char stamps** `@@_/_@@` on a diagonal tile lattice.

## Stamp (one floor tile)

```
@@_   ← 3 columns, 2 rows in char cells
_@@
```

Four `@` cells = four glyph positions of this tile.

- **Stamp:** `STAMP_PREVIEW = ("@@_/_@@", "_@@")` in `src/constants.py`
- **Tip:** `stamp_tip(tx, ty) = (tx − ty, tx + ty)` in tessellation char space
- **Origin:** `stamp_origin(tx, ty) = tip − (1, 1)`
- **Neighbors:** six shared-edge tiles via `tile_neighbors()` on `(tx, ty)` indices

## Scale

| Axis | Tiles per meter |
|------|-----------------|
| XY   | 5 (`TILES_PER_M_XY`) |
| Z    | 10 (`TILES_PER_M_Z`, `ISO_Z_CHARS_PER_M`) |

Editor floor: **5×5 tiles** = continuous **1 m × 1 m** patch in world tile coordinates, centered on the character feet.

## What `EDITOR_FLOOR_5X5_TILE_REFERENCE` is

**Layout sketch** of that 5×5 patch **as seen on screen** — ASCII diamond, **no row gaps**.

You provided this as **раскладка**, not glyph samples (`глиф одинаковый` in game; letters mark tile positions in the test only):

```
____kk_____________
___ggkkpp__________
...
aabbeehhmmqquuwwyy_
```

| Rule | Meaning |
|------|---------|
| 25 tiles | 25 different letters (`a`…`y` in the golden) |
| 4 copies each | **100** non-`_` chars = one letter per `@` cell of that tile’s 3×2 stamp |
| `aa`, `kk` on a row | Two `@` cells of the **same** tile adjacent on that ASCII row — not “one wide cell” |
| `_` | Padding outside the diamond |
| 19×10 | Bounding box of the packed sketch |

Golden: `EDITOR_FLOOR_5X5_TILE_REFERENCE`. Placement: `compute_tile_slot_view()`. Labels: `TILE_SLOT_DISPLAY` (one letter per `(tx, ty)` on each visible `@`).

Runtime editor draw uses grass on iso footprints — the alphabet sketch is a **layout test**, not a grass screenshot.

### 3×2 stamp vs screen projection (2:1 steps)

Do not mix these:

| | **3×2 stamp** | **2:1 steps** (`ISO_STEP_X=2`, `ISO_STEP_Y=1`) |
|---|---------------|--------------------------------------------------|
| What | Size/shape of **one tile** in char cells | How char coords map to **screen** when pygame draws (`IsoProjector`, `floor_screen_offset`) |
| Used for | Tessellation, adjacency, layout golden | Runtime rendering only |

The layout golden is defined by stamp geometry and screen placement rules — not by reading the 2:1 formula off the ASCII.

## Orientation test — 2×2 patch

Smaller golden for **stamp slot order**: all **16** `@` slots, **one** letter each (four distinct letters per tile). Do not reuse 5×5 rules here.

Golden: `EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE` (`render_orientation_packed_sketch`).

```
_ef____
abhgmn_
_dcijpo
____lk_
```

## Walking vs tessellation

| | Directions | Coordinates |
|---|------------|-------------|
| **Tessellation** | 6 neighbors | `(tx, ty)` tile indices |
| **Overworld walk** | 4 screen-aligned steps (↑↓←→ → world diagonals) | `(wx, wy)` via `IsoProjector.screen_delta_to_world` |

Six tessellation neighbors describe **which floor tiles touch**. Four walk directions match **keyboard / screen** in the overworld. Editor floor movement may later align to 6 tessellation steps — separate design choice.

## References

- 2×2 tessellation char union: `DIAG_2X2_SKETCH` in `tessellation.py`
- 5×5 layout sketch: `EDITOR_FLOOR_5X5_TILE_REFERENCE`
- 2×2 orientation sketch: `EDITOR_FLOOR_2X2_ORIENTATION_REFERENCE`
- Character editor: `docs/CHARACTER_EDITOR.md`
