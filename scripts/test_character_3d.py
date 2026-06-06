#!/usr/bin/env python3
"""Full-window 3D voxel character viewer.

Run:
  python scripts/test_character_3d.py
  python scripts/test_character_3d.py --race elf --age 120
  python scripts/test_character_3d.py --equip ash_blade,helm_ash
"""
from __future__ import annotations

import argparse
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.characters.anim import AnimPlayer
from src.characters.bake import bake_pose_set
from src.characters.limb_legend import draw_limb_legend
from src.characters.loader import load_races_catalog
from src.characters.spec import CharacterSpec
from src.constants import init_paths
from src.prototype.dia_scale.display_scale import PRESET_NORMAL, WINDOW_PX_H, WINDOW_PX_W
from src.prototype.dia_scale.slice_view import SLICE_VIEW_LABELS, SliceViewMode, cycle_slice_view_mode
from src.prototype.dia_scale.voxel_3d_renderer import Voxel3DRenderer

EQUIP_KEYS = [
    ("1", "head", "helm_ash"),
    ("2", "hand_r", "ash_blade"),
    ("3", "hand_r", "root_staff"),
    ("4", "hand_l", "pepel_lantern"),
    ("5", "chest", "ash_tunic"),
    ("6", "legs", "root_greaves"),
    ("7", "amulet", "star_amulet"),
]


def _wheel_steps(ev: pygame.event.Event) -> int:
    if getattr(ev, "precise_y", 0):
        return int(round(ev.precise_y))
    y = ev.y
    if y == 0:
        return 0
    return y // 120 or (1 if y > 0 else -1)


def _clamp_slice_z(z: int, z_max: int) -> int:
    return max(0, min(z_max, z))


def _race_list() -> list[str]:
    return sorted(load_races_catalog().keys())


def _parse_equip(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    out: dict[str, str] = {}
    from src.characters.loader import load_equipment_visuals

    items = load_equipment_visuals().get("items", {})
    for part in raw.split(","):
        iid = part.strip()
        if iid in items:
            out[items[iid]["slot"]] = iid
    return out


def _build_spec(args, race_id: str, age: float, seed: int, equipment: dict[str, str | None]) -> CharacterSpec:
    return CharacterSpec(
        race_id=race_id,
        seed=seed,
        age_years=age,
        sex=args.sex,
        equipment=equipment,
    )


def _rebuild(spec: CharacterSpec) -> tuple[CharacterSpec, object, AnimPlayer]:
    pose_set = bake_pose_set(spec, anchor_x=0, anchor_y=0)
    return spec, pose_set, AnimPlayer(pose_set)


def run_interactive(args: argparse.Namespace) -> int:
    init_paths(ROOT)
    pygame.init()
    race_id = args.race
    age_years = args.age
    seed = args.seed
    equipment: dict[str, str | None] = _parse_equip(args.equip)
    spec = _build_spec(args, race_id, age_years, seed, equipment)
    _spec, pose_set, anim = _rebuild(spec)
    auto_walk = not args.no_walk
    anim.set_walking(auto_walk)

    renderer = Voxel3DRenderer(preset=PRESET_NORMAL, hud_font_size=16)
    slice_view: SliceViewMode = "off"
    section_plane = "yz"
    section_coord = 0
    top_slice_z = 10

    screen = pygame.display.set_mode((WINDOW_PX_W, WINDOW_PX_H))
    pygame.display.set_caption(
        "test_character_3d — Tab race | [/] age | R seed | 1-7 equip | Space walk | RMB orbit"
    )

    running = True
    drag_mode: str | None = None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEWHEEL:
                steps = _wheel_steps(ev)
                if not steps:
                    continue
                model = anim.current_model()
                if slice_view == "off":
                    renderer.orbit.zoom_wheel(steps)
                else:
                    top_slice_z = _clamp_slice_z(top_slice_z + steps, model.max_z())
                    if slice_view == "slice":
                        section_coord += steps
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:
                    drag_mode = "orbit"
                elif ev.button in (1, 2):
                    drag_mode = "pan"
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button in (1, 2, 3):
                    drag_mode = None
            elif ev.type == pygame.MOUSEMOTION:
                if not drag_mode:
                    continue
                if drag_mode == "orbit" and ev.buttons[2]:
                    renderer.orbit.rotate_drag(ev.rel[0], ev.rel[1])
                elif drag_mode == "pan" and (ev.buttons[0] or ev.buttons[1]):
                    renderer.orbit.pan_pixels(ev.rel[0], ev.rel[1])
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_TAB:
                    ids = _race_list()
                    i = (ids.index(race_id) + 1) % len(ids) if race_id in ids else 0
                    race_id = ids[i]
                    spec = _build_spec(args, race_id, age_years, seed, equipment)
                    _spec, pose_set, anim = _rebuild(spec)
                    anim.set_walking(auto_walk)
                    top_slice_z = pose_set.get("idle_s").max_z() // 2
                elif ev.key == pygame.K_LEFTBRACKET:
                    age_years = max(1, age_years - 5)
                    spec = _build_spec(args, race_id, age_years, seed, equipment)
                    _spec, pose_set, anim = _rebuild(spec)
                    anim.set_walking(auto_walk)
                elif ev.key == pygame.K_RIGHTBRACKET:
                    age_years += 5
                    spec = _build_spec(args, race_id, age_years, seed, equipment)
                    _spec, pose_set, anim = _rebuild(spec)
                    anim.set_walking(auto_walk)
                elif ev.key == pygame.K_r:
                    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
                    spec = _build_spec(args, race_id, age_years, seed, equipment)
                    _spec, pose_set, anim = _rebuild(spec)
                    anim.set_walking(auto_walk)
                    renderer.reset_view()
                elif ev.key == pygame.K_HOME:
                    renderer.reset_view()
                elif ev.key == pygame.K_SPACE:
                    auto_walk = not auto_walk
                    anim.set_walking(auto_walk)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    anim.set_facing("n")
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    anim.set_facing("s")
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    anim.set_facing("w")
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    anim.set_facing("e")
                elif ev.key == pygame.K_k:
                    slice_view = cycle_slice_view_mode(slice_view)
                elif ev.unicode in {k for k, _s, _i in EQUIP_KEYS}:
                    for key, slot, iid in EQUIP_KEYS:
                        if ev.unicode == key:
                            if equipment.get(slot) == iid:
                                equipment.pop(slot, None)
                            else:
                                equipment[slot] = iid
                            spec = _build_spec(args, race_id, age_years, seed, equipment)
                            _spec, pose_set, anim = _rebuild(spec)
                            anim.set_walking(auto_walk)
                            break

        model = anim.current_model()
        race = load_races_catalog()[race_id]
        mode_txt = (
            f"proj {section_plane.upper()}"
            if slice_view == "off"
            else f"{SLICE_VIEW_LABELS[slice_view]} Z={top_slice_z} {section_plane.upper()}@{section_coord}"
        )
        walk_label = "WALK" if auto_walk else "IDLE"
        hud = [
            f"race={race_id} age={age_years:.0f} seed={seed}  [{walk_label} phase {anim.walk_phase()}]",
            f"facing={anim.facing} pose={anim.current_pose_id()} equip={list(equipment.values())}",
            f"{mode_txt}  {_orbit_label(renderer)}",
            "WASD/стрелки facing  Space walk  Tab race  [/] age  R seed  RMB orbit",
        ]
        top_slice_z = min(top_slice_z, model.max_z())
        surf = renderer.render(
            model,
            title=f"{race.display_name} ({race_id})",
            hud_lines=hud,
            slice_view=slice_view,
            section_plane=section_plane,
            section_coord=section_coord,
            top_slice_z=top_slice_z,
        )
        title_h = renderer._font_hud.get_height() + 6
        draw_limb_legend(surf, y=8 + title_h, font=renderer._font_hud)
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        time.sleep(1.0 / 60)

    pygame.quit()
    return 0


def _orbit_label(renderer: Voxel3DRenderer) -> str:
    o = renderer.orbit
    return (
        f"yaw={math.degrees(o.yaw):.0f} pitch={math.degrees(o.pitch):.0f} "
        f"roll={math.degrees(o.roll):.0f} zoom={o.zoom:.1f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="3D voxel character viewer")
    parser.add_argument("--race", default="human")
    parser.add_argument("--age", type=float, default=28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sex", default="neutral", choices=["male", "female", "neutral"])
    parser.add_argument("--equip", default="", help="comma-separated item ids")
    parser.add_argument("--no-walk", action="store_true", help="start in idle pose")
    args = parser.parse_args()
    init_paths(ROOT)
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
