"""Multi-character isometric tile stamps."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from src import constants
from src.constants import COLOR_DUNGEON_WALL, COLOR_GRASS, COLOR_GRASS_FG, COLOR_TORCH
from src.render.screen_buffer import FOG_EXPLORED, FOG_UNEXPLORED


@dataclass(frozen=True)
class Glyph:
    dx: int
    dy: int
    ch: str


@dataclass
class TileStencil:
    glyphs: list[Glyph]
    default_fg: tuple[int, int, int]
    default_bg: tuple[int, int, int]


@dataclass
class SpriteStencil:
    glyphs: list[Glyph]
    default_fg: tuple[int, int, int]
    default_bg: tuple[int, int, int]


def _tiles_dir() -> str:
    if constants.DATA_DIR is None:
        raise RuntimeError("init_paths() required")
    return os.path.join(constants.DATA_DIR, "art", "tiles")


def _parse_stencil_lines(
    lines: list[str],
    default_fg: tuple[int, int, int],
    default_bg: tuple[int, int, int],
) -> TileStencil:
    glyphs: list[Glyph] = []
    height = len(lines)
    for row, line in enumerate(lines):
        dy = row - (height - 1)
        width = len(line)
        for col, ch in enumerate(line):
            if ch == " ":
                continue
            dx = col - (width - 1) // 2
            glyphs.append(Glyph(dx, dy, ch))
    return TileStencil(glyphs=glyphs, default_fg=default_fg, default_bg=default_bg)


def _procedural_stencil(stencil_id: str) -> TileStencil | None:
    from src.render.procedural_stencil import procedural_tree_canopy, procedural_tree_trunk

    if stencil_id.startswith("tree_canopy_v"):
        parts = stencil_id.split("_")
        try:
            variant = int(parts[2][1:])
            height = int(parts[3][1:])
            radius = int(parts[4][1:])
        except (IndexError, ValueError):
            variant, height, radius = 0, 5, 2
        return procedural_tree_canopy(variant, height, radius)
    if stencil_id == "tree_trunk_slim":
        return procedural_tree_trunk(False)
    if stencil_id == "tree_trunk_thick":
        return procedural_tree_trunk(True)
    return None


@lru_cache(maxsize=128)
def load_tile_stencil(stencil_id: str) -> TileStencil:
    proc = _procedural_stencil(stencil_id)
    if proc is not None:
        return proc
    path = os.path.join(_tiles_dir(), f"{stencil_id}.txt")
    fg, bg = COLOR_GRASS_FG, COLOR_GRASS
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f.readlines() if ln.strip()]
        return _parse_stencil_lines(lines, fg, bg)
    return _fallback_stencil(stencil_id)


def _fallback_stencil(stencil_id: str) -> TileStencil:
    if stencil_id == "wall":
        lines = ["####", "####", "####"]
        return _parse_stencil_lines(lines, (90, 90, 100), COLOR_DUNGEON_WALL)
    if stencil_id == "tree":
        lines = [" T ", "TTT", "/|\\"]
        return _parse_stencil_lines(lines, (80, 140, 80), (20, 40, 20))
    lines = [" .. ", "....", "...."]
    return _parse_stencil_lines(lines, COLOR_GRASS_FG, COLOR_GRASS)


@lru_cache(maxsize=8)
def load_sprite(sprite_id: str) -> SpriteStencil:
    path = os.path.join(_tiles_dir(), f"{sprite_id}.txt")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f.readlines() if ln.strip()]
        t = _parse_stencil_lines(lines, (255, 220, 120), (8, 8, 18))
        return SpriteStencil(t.glyphs, t.default_fg, t.default_bg)
    lines = [" @ ", "/|\\", "/ \\"]
    t = _parse_stencil_lines(lines, (255, 220, 120), (8, 8, 18))
    return SpriteStencil(t.glyphs, t.default_fg, t.default_bg)


# Optional stencil_id in biomes.json; char is fallback key.
CHAR_STENCIL: dict[str, str] = {
    ".": "grass",
    ",": "grass_dry",
    ":": "ridge",
    "+": "ruins",
    "=": "road",
    "T": "tree",
    "#": "wall",
    "o": "herb",
    "O": "herb",
    "*": "shard",
    "~": "water",
    "$": "loot",
    "&": "forge",
    ">": "stairs_down",
    "<": "stairs_up",
    "!": "battle",
    "@": "elder_station",
    "l": "torch",
    "i": "torch",
    "1": "floor",
    "2": "floor",
}


@lru_cache(maxsize=1)
def _biome_floor_stencils() -> dict[str, str]:
    from src.data.art_loader import load_biomes

    out: dict[str, str] = {}
    for biome in load_biomes().values():
        floor = biome.get("floor", ".")
        sid = biome.get("stencil_id")
        if sid:
            out[floor] = sid
    return out


def stencil_id_for_char(ch: str, layer: str, fg: tuple, bg: tuple) -> str:
    biome_map = _biome_floor_stencils()
    if ch in biome_map:
        return biome_map[ch]
    if ch in CHAR_STENCIL:
        return CHAR_STENCIL[ch]
    if layer == "dungeon" and ch in "%#|":
        return "wall"
    return "grass"


def stamp(
    buf,
    anchor_x: int,
    anchor_y: int,
    stencil: TileStencil | SpriteStencil,
    *,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
    light: float = 1.0,
    fog: int = 0,
    fill_iso_footprint: bool = False,
) -> None:
    use_fg = fg if fg is not None else stencil.default_fg
    use_bg = bg if bg is not None else stencil.default_bg
    if fill_iso_footprint:
        from src.render.iso_projector import IsoProjector

        fill_ch = "y" if use_fg[1] > use_fg[0] else "."
        for fx, fy in IsoProjector().footprint_char_cells(anchor_x, anchor_y):
            if fog:
                buf.set_fog(fx, fy, fog)
            buf.set(fx, fy, fill_ch, fg=use_fg, bg=use_bg, light=light)
    for g in stencil.glyphs:
        x, y = anchor_x + g.dx, anchor_y + g.dy
        if fog:
            buf.set_fog(x, y, fog)
        buf.set(x, y, g.ch, fg=use_fg, bg=use_bg, light=light)
