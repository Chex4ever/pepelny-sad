# Level editor

Default render: **CPU**. Viewport: **diag 3×2 stamp + packed diamond** (`docs/ISO_LAYOUT.md`) — same as character editor floor, **not** overworld `IsoProjector` footprint.

## Layout

Same window size as `character_editor`:

| Zone | Content |
|------|---------|
| Left | Palette tree (tools, floor stencils, structures, vegetation, generators) |
| Center | Iso viewport (WYSIWYG) |
| Right | Inspector — tool, patch, selected **diag tile** (4 @ slots) |
| Bottom | Status bar |

**Выделение** (инструмент по умолчанию): клик выделяет **тайл** целиком. В свойствах — один **шаблон** (stencil из палитры «Пол»); кнопка «Перейти к объекту в палитре».

`+Y` here is **north** on the diag lattice (opposite tessellation `ty` index in the golden sketch). The **5×5 golden** in character editor is a **layout reference**, not tiles grouped by metre.

**Как читать оси на экране** — эталонные силуэты (цифра = координата тайла по оси, `_` = пустая ячейка): см. [Axis silhouettes](ISO_LAYOUT.md#axis-silhouettes-on-the-packed-screen) в `ISO_LAYOUT.md`.

Default patch: **5 m** (25×25 diag tiles). Each tile placed individually on one diag diamond canvas.

## Run

```bash
python scripts/level_editor.py
python scripts/level_editor.py --load maps/my_map.json
python scripts/level_editor.py --size 32 --seed 100
```

Maps save to `maps/*.json` (Ctrl+S).

## Controls

| Input | Action |
|-------|--------|
| **LMB** (viewport) | Select tile (Выделение) or paint/place (other tools) |
| **RMB** (viewport) | Erase tile (not in Select mode) |
| **Palette** | Tool, stencil, structure, vegetation, generators |
| **G** | Fill bounds with current biome |
| **R** | New seed + biome fill with trees |
| **+ / −** | Patch size |
| **Arrows / WASD** | Pan focus (outside viewport) |
| **Ctrl+S** | Save |
| **Ctrl+O** | Load |
| **N** | New blank map |
| **Esc** | Quit |

## Map format (`EditorDocument`)

JSON in `maps/`:

- `version`, `seed`, `bounds` (`wx0`, `wy0`, `width`, `height`)
- `chunks[]`: `tiles`, `fg`, `bg`, `floor_stencils`, `cell_solids`, `structure_anchors`

Model matches [`Chunk`](src/world/chunk.py) storage.

## Architecture

```
level_editor UI → EditorTools / generators → EditableWorld (EditorDocument)
                                            → build_world_packed_draw_map
                                            → draw_diag_viewport (CPU pygame)
```

- **Not in MVP:** dungeon editing, F5 game save, undo.
- **Generators:** `fill_biome`, `paint_road`, `make_clearing`, `scatter_trees`, `scatter_bushes_in_bounds` in `src/world/editor/generators.py`.

## Performance

Default patch 25×25 redraws **2500** packed cells every frame. Profiling and optimization plan: [`LEVEL_EDITOR_PERFORMANCE.md`](LEVEL_EDITOR_PERFORMANCE.md).

```bash
python scripts/profile_level_editor.py --frames 30
```

## Related docs

- [`ENGINE.md`](ENGINE.md) — render engine layers
- [`ISO_LAYOUT.md`](ISO_LAYOUT.md) — packed vs iso projection
- [`CHARACTER_EDITOR.md`](CHARACTER_EDITOR.md) — character tool (1 m packed floor)
- [`LEVEL_EDITOR_PERFORMANCE.md`](LEVEL_EDITOR_PERFORMANCE.md) — frame budget and optimization roadmap
