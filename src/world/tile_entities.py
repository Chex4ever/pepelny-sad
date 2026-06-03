"""Resolve world tiles and entities for examine/tooltip."""
from __future__ import annotations

from src.data.art_loader import load_items, load_materials

_TILE_STATIC = {
    "o": ("Серая трава", "grey_herb"),
    "+": ("Корневое волокно", "root_fiber"),
    "*": ("Осколок звезды", "star_shard"),
    "$": ("Комок пепла", "ash_clump"),
    "&": ("Кузня Пепла", "elder"),
    "~": ("Ткацкий станок", "elder"),
    ">": ("Спуск в подземелье", "elion"),
    "<": ("Выход на поверхность", "elion"),
    "@": ("Старейшина пепла", "elder"),
    "T": ("Увядшее дерево", "elion"),
    ".": ("Серая трава", "grey_herb"),
    ",": ("Пепельная степь", "grey_herb"),
    "l": ("Факел", "elion"),
    "i": ("Факел", "elion"),
}

_COMPANION_ART = {
    "whisper_companion": ("Шёпот", "whisper_companion"),
    "sorrow_companion": ("Скорбь-искра", "sorrow_companion"),
}


def resolve_battle_enemy(wx: int, wy: int, layer: str, game) -> tuple[str, str] | None:
    ch, _, _ = game.world_map.get_tile(wx, wy, layer)
    if ch != "!":
        return None
    if layer == "dungeon":
        name = "Страж Корней" if game.world_state.dungeon_entered else "Скорбь-искра"
        art = "warden" if game.world_state.dungeon_entered else "sorrow"
        return name, art
    if wy > 30:
        return "Скорбь-искра", "sorrow"
    return "Шёпот", "whisper"


def resolve_world_cell(wx: int, wy: int, layer: str, game) -> tuple[str, str] | None:
    """Return (display_name, art_id) for cell."""
    ch, _, _ = game.world_map.get_tile(wx, wy, layer)
    if ch == "!":
        return resolve_battle_enemy(wx, wy, layer, game)
    if ch in _TILE_STATIC:
        return _TILE_STATIC[ch]
    if ch in load_materials():
        mat = load_materials()[ch]
        return mat.get("name", ch), ch
    return None


def resolve_companion(cid: str) -> tuple[str, str]:
    return _COMPANION_ART.get(cid, (cid, cid))


def resolve_player() -> tuple[str, str]:
    return "Элион", "elion"


def resolve_inventory_item(item_id: str) -> tuple[str, str]:
    items = load_items()
    mats = load_materials()
    if item_id in items:
        d = items[item_id]
        return d.get("name", item_id), d.get("art_id", item_id)
    if item_id in mats:
        d = mats[item_id]
        return d.get("name", item_id), d.get("art_id", item_id)
    return item_id, item_id
