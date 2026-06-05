# Производительность (v0.3)

Документ фиксирует **цели**, **замеры**, **тесты** и **план оптимизации** для «Пепельного Сада».  
Версия 0.3 — первая, где производительность overworld считается обязательным критерием merge.

## Два уровня целей

| Уровень | Метрика | Цель | Комментарий |
|---------|---------|------|-------------|
| **Минимум (играбельно)** | GPU `map_draw` | **&lt; 16 ms** mean | Логика карты + GL stamp; 60 FPS |
| **Минимум (играбельно)** | GPU полный кадр (без vsync-wait) | **&lt; 16 ms** mean, **&lt; 24 ms** p95 | `PEPELNY_PERF_MEAN_MS` / `PEPELNY_PERF_P95_MS` |
| **Минимум** | FOV LOS (r≈32) | **&lt; 10 ms** mean | `PEPELNY_FOV_LOS_MS` |
| **Минимум** | Отклик ввода | **&lt; 1 ms** | Смена состояния/позиции в `handle_input` до отрисовки |
| **Максимум (идеал)** | Весь кадр | **1 ms** | ~1000 FPS; **нереалистично** для Python+полный overworld; ориентир для **input-only** фазы |
| **Debug (iso CPU)** | Полный кадр | **&lt; 165 ms** mean | Только отладка; `stamp()` по ~2200 глифам — не целевой путь |

**Важно:** в F4 HUD строка **Present / GPU: flip** часто показывает **ожидание vsync** (300–400 ms при 60 Hz), а не медленную логику. Для регрессий смотрите **`map_draw`**, **`map_queue`**, **`fov_los`** — они отражают реальную работу CPU/GPU.

## Где лежат тесты

```
tests/performance/
├── conftest.py                      # BenchGame, SDL dummy для iso
├── test_overworld_walk_perf.py      # iso walk: mean/p95 кадра + fov_los
├── test_overworld_pan_perf.py       # панорама без FOV (кэш очереди)
├── test_overworld_gpu_perf.py       # GPU map_draw (без flip); skip без GL
├── test_fov_visible_radius_budget.py # shadowcast при VISIBLE_LOS_RADIUS_SURFACE
└── test_fov_radius_100_budget.py  # legacy r=100 (регрессия, не gameplay)
```

Скрипт локального отчёта:

```bash
python scripts/run_perf_benchmark.py
PEPELNY_RENDER=gpu python scripts/run_perf_benchmark.py
PEPELNY_PERF_REPORT=assets/debug/baseline_iso.json python scripts/run_perf_benchmark.py
```

F4 в игре — live HUD (`PEPELNY_PERF=1` — лог медленных кадров в консоль).

## Бюджеты в CI (env по умолчанию)

| Переменная | GPU | iso (debug) |
|------------|-----|-------------|
| `PEPELNY_PERF_MEAN_MS` | 16 | 165 |
| `PEPELNY_PERF_P95_MS` | 24 | 260 |
| `PEPELNY_FOV_LOS_MS` | 10 | 10 |
| `PEPELNY_GPU_MAP_MS` | 25 | — |
| `PEPELNY_SYNC_BUDGET_MS` | 2 | 2 |

Команды:

```bash
python -m pytest tests/performance/ -q          # все perf-тесты
python -m pytest tests/performance/ -m "not slow" -q  # быстрые (FOV)
python -m pytest tests/ -q                        # полный CI (включая perf)
```

## Последние замеры

### Baseline iso (CI / dummy SDL)

Файл: [`assets/debug/baseline_iso.json`](../assets/debug/baseline_iso.json)  
Сценарий: seed 4242, walk down, 40 measured frames, `PEPELNY_RENDER=iso`.

| Метрика | Значение |
|---------|----------|
| mean frame | **122.2 ms** |
| p95 frame | 182.7 ms |
| **fov_los** | **9.3 ms** |
| map_queue | 15.0 ms |
| map_draw (stamp) | 116.0 ms |
| draw_queue / stamp | ~2218 глифов/кадр |

FOV после split r=100→32: было до **~100 ms** на шаг; сейчас укладывается в бюджет.

### In-game GPU (Windows, F4 HUD)

Режим: `PEPELNY_RENDER=gpu`, overworld surface, 53 chunks.

| Stage | ms | Доля |
|-------|-----|------|
| Present / flip | ~388 | vsync-wait (не логика) |
| **map_draw** | **~12** | реальная отрисовка карты |
| **map_queue** | **~11** | сбор очереди |
| Draw overworld | ~16 | |
| UI | ~4 | |

Счётчики: `draw_queue≈2141`, **`gpu_q≈43758`** — главный кандидат на оптимизацию 0.3.x (батчинг / culling).

Полный кадр **309–427 ms** в HUD — из‑за Present; **игровая логика ~12–16 ms**.

## Политика PR

**Любое изменение**, затрагивающее overworld, рендер, FOV, чанки или ввод:

1. `python -m pytest tests/performance/ -q` — зелёный
2. При смене бюджетов — обновить этот файл и `baseline_*.json`
3. PR **не мержить**, если perf-тесты красные или mean frame / fov_los вышли за бюджет без явного обоснования в описании PR

См. также `.cursor/rules/testing.mdc`.

## Что уже сделано (0.3.0)

- FOV: `VISIBLE_LOS_RADIUS_SURFACE=32`, explored персистентный, recompute на смене tile
- Кэш `draw_queue` в `MapRenderer`
- Surface shadows off по умолчанию (`PEPELNY_SURFACE_SHADOWS=0`)
- Фоновые чанки (`PEPELNY_RUNTIME_CHUNK_WORKERS`)
- Плавное движение: float позиция, `world_time_s`, camera lerp
- Held WASD + repeat через `LocomotionController`
- GPU-путь + perf benchmark / F4 stages

## План оптимизации (0.3.x → 0.4)

### P0 — измерения и HUD

1. **Разделить Present в F4**: `map_draw` vs `swap_buffers` vs `vsync_wait` — чтобы не путать 400 ms flip с 12 ms логикой.
2. **Зафиксировать GPU baseline** на машине разработчика: `baseline_gpu.json` (map_draw, gpu_q).
3. Добавить счётчик **input phase** в perf HUD (&lt;1 ms gate).

### P1 — GPU draw call storm (`gpu_q` 40k+)

1. **Instancing / mega-buffer** — один draw call на слой вместо квада на глиф.
2. **Viewport culling** — не ставить в очередь тайлы вне экрана + margin.
3. **LOD для деревьев** — дальние `T` как один глиф / billboards.
4. Снизить `draw_queue` с ~2141 до &lt;800 без потери картинки.

### P2 — CPU очередь и FOV

1. Расширить кэш queue: инвалидация только по `visible_version` + dirty chunks.
2. `get_column` memo на чанк-поколение (сейчас ~1800 вызовов/кадр).
3. GPU FOV texture (`PEPELNY_GPU_FOV=1`) — только если `fov_los` &gt;10 ms на целевых машинах.

### P3 — streaming и sync

1. Предзагрузка чанков по вектору движения (1–2 чанка вперёд).
2. `PEPELNY_SYNC_BUDGET_MS=2` — жёстче в тестах при росте мира.
3. Occluder texture при загрузке чанка (для будущего GPU FOV).

### P4 — продуктовые настройки

1. **`PEPELNY_RENDER=gpu` по умолчанию** в релизном билде (iso — debug).
2. Quality presets: shadows, FOV radius, chunk workers.
3. Опциональный **uncapped FPS** / `vsync=0` для бенчмарков.

### Критерии готовности 0.4

| Метрика | Цель |
|---------|------|
| GPU `map_draw` mean | **&lt; 8 ms** |
| GPU `gpu_q` | **&lt; 15000** |
| FOV `fov_los` | **&lt; 5 ms** |
| Input phase | **&lt; 1 ms** p95 |
| In-game FPS (vsync on) | стабильные **60** без просадок при ходьбе |

## Ссылки в коде

- Бюджеты: `src/core/perf_benchmark.py` — `default_budget_ms`, `default_fov_los_budget_ms`
- Бенчмарк: `scripts/run_perf_benchmark.py`
- FOV: `src/scenes/overworld/fov_controller.py`, `src/constants.py`
- Очередь: `src/scenes/overworld/map_renderer.py`
- GPU: `src/render/gpu/iso_renderer.py`, `src/render/gpu/presenter.py`
