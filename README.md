# Пепельный Сад

Демо-игра на Pygame в духе Undertale × COGMIND × Terraria: исследование чанкового мира, Soul Scan в боях, крафт и ASCII-портреты.

## Установка

```bash
pip install -r requirements.txt
python main.py
```

Python 3.11+, Pygame 2.5+.

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
| Overworld | WASD — ход, E — действие/сбор, Tab — персонаж, F5 — сохранение, F9 — загрузка |
| Character sheet | стрелки — слот, Enter — экипировать, O — осмотр, Esc/Tab — закрыть |
| Craft | Enter — крафт, O — осмотр, Esc — закрыть |
| Battle | стрелки — меню, Enter — выбор, O — осмотр врага |
| Dodge | WASD — душа |
| Fight QTE | Space — удар в зелёной зоне |
| Global | Esc — назад/закрыть overlay |

## Лор (без спойлеров)

Элион — хранитель увядшего святилища — ищет последнюю искру **Лиры** в Степях Пепла. На поверхности ещё видны закаты; под землёй — **Сад Пепла**, где бои идут по правилам души, а не только стали.

Слушай ветер (Act), spare врагов ради компаньонов, крафти снаряжение у Кузни и следуй к Перекрёстку Ив.

## Tile legend

`>` вход в подземелье, `<` выход, `T` дерево, `l`/`i` факел, `$` лут, `&` Кузня, `~` станок, `o`/`+` ресурсы, `!` бой, `@` сюжетный NPC, `=` дорога.

## Референсы

Undertale (бой/Mercy), COGMIND (ASCII UI, осмотр), Minecraft (чанки), Diablo (экипировка, сегменты), No Man's Sky (слоты), Terraria (крафт).
