# Редактор генератора персонажей

Инструмент для настройки **процедурного генератора** и создания **конкретных персонажей** с iso-stencil превью (10×16 px на глиф, как в игре).

## Запуск

```bash
python scripts/character_editor.py
python scripts/character_editor.py --race dwarf --age 50 --seed 7
python scripts/character_editor.py --age-preset elder
```

Аргументы: `--race`, `--age`, `--seed`, `--sex`, `--age-preset` (child/young/adult/elder).

Legacy-тuner (3D orbit): `scripts/test_character_tuner.py`.

## Раскладка окна

```
┌──────────┬─────────────────────────────┬──────────────┐
│ Части    │  Iso preview (fixed cam)    │ Раса/возраст │
│ дерева   │  + диагностика + paint      │ + параметры  │
├──────────┴─────────────────────────────┴──────────────┤
│ Панель анимации: pause, walk, phase, speed, facing  │
└───────────────────────────────────────────────────────┘
```

## Два режима (клавиша **M**)

### Generator (по умолчанию)

**Цель:** править поведение генератора и убирать аномалии.

1. Меняйте race/age/seed (**R** — новый seed) и ищите артефакты.
2. Смотрите диагностику: `s` / `a` / `e` в HUD и на модели.
3. В правой панели фиксируйте override параметра (кнопки ±, поле value, ref).
4. **Export** → `exports/tuning_overrides.json` + diff.

Voxel-edits в этом режиме — для превью; основной артеfact — tuning overrides.

### Character

**Цель:** конкретный персонаж + анимации.

1. Параметры генератора свёрнуты (read-only).
2. LMB/RMB — правка вокселей, export включает `exports/voxel_edits.json`.
3. Проверяйте walk-кадры (A/S), facings (Z/X), пауза (Space).

## Управление

| Клавиша | Действие |
|---------|----------|
| **Z** / **X** | Поворот персонажа −45° / +45° (8 направлений) |
| **A** / **S** | Предыдущий / следующий кадр анимации |
| **Space** | Пауза / продолжить |
| **← → ↑ ↓** | Сдвинуть выделенный воксель (X/Y) |
| **PgUp / PgDn** | Сдвинуть выделенный воксель по Z |
| **LMB** | Выделить воксель или создать + выделить |
| **RMB** | Удалить воксель под курсором |
| **Esc** | Снять выделение |
| **M** | Generator ↔ Character |
| **R** | Новый seed |

Камера **не вращается** — фиксированный игровой pitch/yaw.

## 3D-редактирование глифов

1. **LMB по глифу** — выделение; kind синхронизируется с левой панелью.
2. **LMB по пустому месту** — новый воксель выбранного kind на слое Z (выделенный или пол).
3. **Стрелки / PgUp/PgDn** — перемещение выделенного вокселя в model space.
4. **Z/X** — повернуть персонажа, чтобы править «глубину» с другой стороны.
5. **RMB** — удалить воксель.

## Диагностические глифы

| Глиф | Значение |
|------|----------|
| **`s`** (жёлтый, blink) | Разрыв: части тела не соприкасаются или один kind распался на несколько островов |
| **`a`** (красный, blink) | При walk: стопы не касаются пола (воздух под ногами) |
| **`e`** (красный, blink) | Воксель ниже уровня пола |

Счётчик в HUD: `warn: N×s M×a K×e`.

## Пол и масштаб

- Пол: сетка **5×5** тайлов (= 1 м при `TILES_PER_M_XY=5`).
- Персонаж стоит **на полу** (pivot по `floor_z`, не по центру bbox).
- Тени: самозатенение столбцов + силуэт на полу.

## Export

| Файл | Содержимое |
|------|------------|
| `exports/tuning_overrides.json` | Overrides vs reference (generator) |
| `exports/tuning_diff.txt` | Текстовый diff |
| `exports/voxel_edits.json` | Ручные add/remove вокселей (character) |

## Связь с кодом

| Модуль | Назначение |
|--------|------------|
| `scripts/character_editor.py` | Main loop |
| `src/characters/tuning.py` | TuningState, reference, export |
| `src/characters/bake.py` | Canonical pose bake + lazy facing |
| `src/characters/voxel_edits.py` | Manual voxel layer |
| `src/characters/editor_diagnostics.py` | s/a/e markers |
| `src/characters/editor_shading.py` | Column + floor shadows |
| `src/characters/editor_voxel_tools.py` | Select / move / create |
| `src/prototype/dia_scale/iso_character_renderer.py` | Fixed iso preview |

## Roadmap (не реализовано)

- Slice plane (`/`) для покадрового слоя Z
- Symmetry paint (зеркало L/R)
- Batch seed scan (100 seeds → отчёт s/a/e)
- Pitch dev slider только в generator mode
