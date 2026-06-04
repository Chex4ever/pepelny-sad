"""Resolve world tiles and entities for examine/tooltip."""
from __future__ import annotations

from src.data.art_loader import load_items, load_materials
from src.i18n import localized_name, t

_TILE_STATIC = {
    "o": ("tile.grey_herb", "grey_herb_large"),
    "+": ("tile.root_fiber", "root_fiber"),
    "*": ("tile.star_shard", "star_shard"),
    "$": ("tile.ash_clump", "ash_clump"),
    "&": ("tile.ash_forge", "ash_forge"),
    "~": ("tile.loom", "elder"),
    ">": ("tile.dungeon_down", "elion_portrait"),
    "<": ("tile.dungeon_up", "elion_portrait"),
    "@": ("tile.elder", "elder_portrait"),
    "T": ("tile.withered_tree", "grey_herb_large"),
    ".": ("tile.grey_herb", "grey_herb_large"),
    ",": ("tile.ash_steppe", "grey_herb_large"),
    "l": ("tile.torch", "elion"),
    "i": ("tile.torch", "elion"),
}

_COMPANION_ART = {
    "whisper_companion": ("dialogue.speaker.whisper", "whisper_companion"),
    "sorrow_companion": ("dialogue.speaker.sorrow", "sorrow_companion"),
}


def _tile_name(name_key: str) -> str:
    return t(name_key)


def resolve_battle_enemy(wx: int, wy: int, layer: str, game) -> tuple[str, str] | None:
    ch, _, _ = game.world_map.get_tile(wx, wy, layer)
    if ch != "!":
        return None
    if layer == "dungeon":
        name = t("enemy.warden.name") if game.world_state.dungeon_entered else t("enemy.sorrow.name")
        art = "warden" if game.world_state.dungeon_entered else "sorrow_large"
        return name, art
    if wy > 30:
        return t("enemy.sorrow.name"), "sorrow_large"
    return t("enemy.whisper.name"), "whisper"


def resolve_world_cell(wx: int, wy: int, layer: str, game) -> tuple[str, str] | None:
    """Return (display_name, art_id) for cell."""
    ch, _, _ = game.world_map.get_tile(wx, wy, layer)
    if ch == "!":
        return resolve_battle_enemy(wx, wy, layer, game)
    if ch in _TILE_STATIC:
        name_key, art_id = _TILE_STATIC[ch]
        return _tile_name(name_key), art_id
    if ch in load_materials():
        mat = load_materials()[ch]
        return localized_name(mat, ch, "material"), ch
    return None


def resolve_companion(cid: str) -> tuple[str, str]:
    name_key, art = _COMPANION_ART.get(cid, (cid, cid))
    if cid in _COMPANION_ART:
        return t(name_key), art
    return cid, cid


def resolve_player() -> tuple[str, str]:
    return t("character.elion"), "elion_portrait"


def resolve_inventory_item(item_id: str) -> tuple[str, str]:
    items = load_items()
    mats = load_materials()
    if item_id in items:
        d = items[item_id]
        return localized_name(d, item_id, "item"), d.get("art_id", item_id)
    if item_id in mats:
        d = mats[item_id]
        return localized_name(d, item_id, "material"), d.get("art_id", item_id)
    return item_id, item_id
