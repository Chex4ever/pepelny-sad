# Пепельный Сад

[![CI](https://github.com/Chex4ever/pepelny-sad/actions/workflows/ci.yml/badge.svg)](https://github.com/Chex4ever/pepelny-sad/actions/workflows/ci.yml)

Демо-игра на Pygame в духе Undertale × COGMIND × Terraria: исследование чанкового мира, Soul Scan в боях, крафт и ASCII-портреты.

Текущая версия: **0.2.8** (см. файл [`VERSION`](VERSION)).

## Установка

### Из исходников (разработка)

```bash
pip install -r requirements.txt
python main.py
```

Python 3.11+, Pygame 2.5+. Для CI и сборки релизов используется Python **3.12**.

### Windows x64

Скачайте `pepelny-sad-{version}-win-x64-setup.exe` из [Releases](https://github.com/Chex4ever/pepelny-sad/releases) и запустите установщик. Игра ставится в `%ProgramFiles%\Пепельный Сад\`.

### Linux x64

```bash
tar xzf pepelny-sad-{version}-linux-x64.tar.gz
./install.sh --yes
```

По умолчанию: `~/.local/share/pepelny-sad/`, ярлык в `~/.local/share/applications/`, команда `pepelny-sad` в `~/.local/bin/`.

## Версии и релизы

| Событие | Кто | Пример |
|---------|-----|--------|
| Merge в `main` | GitHub Actions (auto patch) | 0.2.8 → 0.2.9 |
| Minor / Major | PR с ручной правкой `VERSION` | 0.2.x → 0.3.0 или 1.0.0 |

- Единый источник версии: файл [`VERSION`](VERSION)
- При каждом merge в `main` workflow [`release.yml`](.github/workflows/release.yml) собирает PyInstaller **onedir**, публикует GitHub Release `vX.Y.Z` и коммитит bump с `[skip ci]`
- Установленная игра (frozen build) при старте тихо проверяет обновления через manifest на GitHub Releases; скачиваются только изменённые файлы

Переменные окружения updater (опционально): `PEPELNY_UPDATE_REPO`, `PEPELNY_UPDATE_PROVIDER`, `PEPELNY_UPDATE_BASE_URL` (для будущего CDN).

## Сборка релиза локально

```bash
pip install -r requirements.txt -r requirements-build.txt
python tools/prepare_audio.py
python tools/build_release.py
```

Результат: `dist/pepelny-sad-{win-x64|linux-x64}/`, `dist/manifest-{platform}.json`.

Windows installer (Inno Setup 6):

```powershell
$v = (Get-Content VERSION).Trim()
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" /DMyAppVersion=$v tools/installer/pepelny_sad.iss
```

## Тесты

```bash
pip install -r requirements-dev.txt
python -m pytest --cov=src --cov-report=term-missing
```

Только unit-тесты: `python -m pytest tests/unit`  
Только интеграционные: `python -m pytest tests/integration -m integration`  
**Регрессия (порядок импортов / `main.py`):** `python -m pytest tests/regression -m regression`

> `conftest.py` вызывает `init_paths()` заранее — это удобно для unit/integration, но **скрывает** баги вроде `DATA_DIR=None`. Регрессионные тесты запускаются в отдельном subprocess без ранней инициализации.

## Управление

| Режим | Клавиши |
|-------|---------|
| Title | Enter — новая игра, R — другой seed, L — загрузка |
| Intro | Enter / Space / клик — далее (побуквенно + голос) · Space удерж. — пропуск |
| Overworld | WASD — ход, E — действие/сбор, Tab — персонаж, F5 — сохранение, F9 — загрузка |
| Overworld мышь | наведение — подсказка в status strip; ЛКМ — осмотр; drag — панорама обзора |
| Overworld UI | LOG и окна осмотра/крафта/персонажа — модальные (drag заголовка, [−] свернуть, [×] закрыть) |
| Layout | карта на весь экран минус 2 строки status strip снизу |
| Character sheet | стрелки — слот, Enter — экипировать, O — осмотр, Esc/Tab — закрыть |
| Craft | Enter — крафт, O — осмотр, Esc — закрыть |
| Battle | стрелки — меню, Enter — выбор, O / ЛКМ на портрете — осмотр врага |
| Dodge | WASD — душа |
| Fight QTE | Space — удар в зелёной зоне |
| Pause (Esc) | главное меню, сохранить, сохранить и выйти, выход без сохранения |
| Help (F1) | подсказка по управлению (кроме title) |
| Fog / LOS | неисследованное — чёрный туман; исследованное вне обзора — dim; враги `!` только в LOS |

Переходы между сценами — короткий fade (~0.5 с). Title-экран анимируется ~5 с (рамка → меню → фон с пеплом).

## Лор (без спойлеров)

Элион — хранитель увядшего святилища — ищет последнюю искру **Лиры** в Степях Пепла. На поверхности ещё видны закаты; под землёй — **Сад Пепла**, где бои идут по правилам души, а не только стали.

Слушай ветер (Act), spare врагов ради компаньонов, крафти снаряжение у Кузни и следуй к Перекрёстку Ив.

## Tile legend

`>` вход в подземелье, `<` выход, `T` дерево, `l`/`i` факел, `$` лут, `&` Кузня, `~` станок, `o`/`+` ресурсы, `!` бой, `@` сюжетный NPC, `=` дорога.

## Audio

Звуки и музыка лежат в `assets/audio/` (см. `manifest.json` и `LICENSES.md`).

**Подготовка ассетов** (Kenney CC0 + процедурные fallback):

```bash
python tools/prepare_audio.py
# или
powershell tools/fetch_audio.ps1
```

С `ffmpeg` в PATH WAV конвертируются в OGG; без ffmpeg используются WAV (pygame поддерживает оба).

- **Шаги** — по поверхности (трава/грязь/гравий/камень/дорога), случайный клип, pitch-варианты, cooldown 120 ms
- **Окружение** — ветер, пепельный шторм, факелы (по дистанции в FOV), пещера + капли
- **Музыка** — crossfade по сцене/слою/погоде/ночи; пауза при Esc-меню

## Референсы

Undertale (бой/Mercy), COGMIND (ASCII UI, осмотр), Minecraft (чанки), Diablo (экипировка, сегменты), No Man's Sky (слоты), Terraria (крафт).
