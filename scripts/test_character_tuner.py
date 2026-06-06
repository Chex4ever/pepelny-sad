#!/usr/bin/env python3
"""Dual-panel character generator tuner with live 3D preview.

Legacy tuner — for full iso-stencil editor see scripts/character_editor.py

Run:
  python scripts/test_character_tuner.py
  python scripts/test_character_tuner.py --race dwarf --age 50 --seed 7
  python scripts/test_character_tuner.py --age-preset elder
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
from src.characters.loader import load_race
from src.characters.morphology import LifeStage
from src.characters.tuning import (
    SpecController,
    TuningState,
    build_current_values,
    build_reference,
    stage_preset_age,
)
from src.characters.tuner_ui import (
    RaceAgeBar,
    Rect,
    SettingsPanel,
    export_to_files,
)
from src.constants import init_paths
from src.prototype.dia_scale.display_scale import (
    PRESET_NORMAL,
    TUNER_LEFT_W,
    TUNER_WINDOW_PX_H,
    TUNER_WINDOW_PX_W,
)
from src.prototype.dia_scale.voxel_3d_renderer import Voxel3DRenderer

DEBOUNCE_S = 0.15


def _wheel_steps(ev: pygame.event.Event) -> int:
    if getattr(ev, "precise_y", 0):
        return int(round(ev.precise_y))
    y = ev.y
    if y == 0:
        return 0
    return y // 120 or (1 if y > 0 else -1)


def _orbit_label(renderer: Voxel3DRenderer) -> str:
    o = renderer.orbit
    return (
        f"yaw={math.degrees(o.yaw):.0f} pitch={math.degrees(o.pitch):.0f} "
        f"roll={math.degrees(o.roll):.0f} zoom={o.zoom:.1f}"
    )


def _apply_age_preset(ctrl: SpecController, preset: str) -> None:
    stage_map = {
        "child": LifeStage.CHILD,
        "young": LifeStage.YOUNG,
        "adult": LifeStage.ADULT,
        "elder": LifeStage.ELDER,
    }
    stage = stage_map.get(preset.lower())
    if stage:
        race = load_race(ctrl.race_id)
        ctrl.age_years = stage_preset_age(race, stage)


def run_interactive(args: argparse.Namespace) -> int:
    init_paths(ROOT)
    pygame.init()

    ctrl = SpecController(
        race_id=args.race,
        age_years=args.age,
        seed=args.seed,
        sex=args.sex,
    )
    if args.age_preset:
        _apply_age_preset(ctrl, args.age_preset)
    ctrl.clamp_age_to_race()

    tuning = TuningState()
    reference = build_reference(ctrl.to_spec())
    current = build_current_values(ctrl.to_spec(), tuning)

    auto_walk = not args.no_walk
    dirty = True
    last_change = 0.0
    rebuilding = False
    pose_set = bake_pose_set(ctrl.to_spec(), tuning=tuning)
    walk_period = float(tuning.get("anim.walk_period_s", 0.36))
    anim = AnimPlayer(pose_set, walk_period_s=walk_period)
    anim.set_walking(auto_walk)
    dirty = False

    renderer = Voxel3DRenderer(preset=PRESET_NORMAL, panel_w=TUNER_LEFT_W, panel_h=TUNER_WINDOW_PX_H, hud_font_size=14)
    race_bar_left = RaceAgeBar(compact=True)
    race_bar_right = RaceAgeBar(compact=False)
    settings = SettingsPanel()

    font = pygame.font.SysFont("segoe ui", 13)
    small = pygame.font.SysFont("segoe ui", 11)
    mono = pygame.font.SysFont("consolas", 10)

    screen = pygame.display.set_mode((TUNER_WINDOW_PX_W, TUNER_WINDOW_PX_H))
    pygame.display.set_caption("character_tuner — live generator tuning")

    left_panel = Rect(0, 0, TUNER_LEFT_W, TUNER_WINDOW_PX_H)
    right_panel = Rect(TUNER_LEFT_W, 0, TUNER_WINDOW_PX_W - TUNER_LEFT_W, TUNER_WINDOW_PX_H)
    race_compact_rect = Rect(0, 0, TUNER_LEFT_W, race_bar_left.height)
    race_full_rect = Rect(TUNER_LEFT_W, 0, right_panel.w, race_bar_right.height)
    settings_rect = Rect(TUNER_LEFT_W, race_bar_right.height, right_panel.w, TUNER_WINDOW_PX_H - race_bar_right.height)

    drag_mode: str | None = None
    running = True

    def mark_dirty() -> None:
        nonlocal dirty, last_change, reference, current
        if tuning.is_locked("spec.race_id"):
            ctrl.race_id = str(tuning.get("spec.race_id", ctrl.race_id))
        if tuning.is_locked("spec.age_years"):
            ctrl.age_years = float(tuning.get("spec.age_years", ctrl.age_years))
        if tuning.is_locked("spec.seed"):
            ctrl.seed = int(tuning.get("spec.seed", ctrl.seed))
        if tuning.is_locked("spec.sex"):
            ctrl.sex = str(tuning.get("spec.sex", ctrl.sex))
        ctrl.clamp_age_to_race()
        dirty = True
        last_change = time.monotonic()
        spec = ctrl.to_spec()
        reference = build_reference(spec)
        current = build_current_values(spec, tuning)

    def on_spec_change() -> None:
        tuning.reset_prefix("race.")
        mark_dirty()

    def do_export(_tuning: TuningState, ref: dict, _ctrl: SpecController) -> None:
        jp, tp = export_to_files(_tuning, ref, _ctrl, export_dir=os.path.join(ROOT, "exports"))
        print(f"Exported: {jp}\n         {tp}")

    while running:
        now = time.monotonic()
        if dirty and now - last_change >= DEBOUNCE_S:
            rebuilding = True
            spec = ctrl.to_spec()
            walk_period = float(tuning.get("anim.walk_period_s", 0.36))
            pose_set = bake_pose_set(spec, tuning=tuning)
            anim = AnimPlayer(pose_set, walk_period_s=walk_period)
            anim.set_walking(auto_walk)
            current = build_current_values(spec, tuning)
            dirty = False
            rebuilding = False

        mx, my = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                continue

            if settings.handle_event(
                ev, tuning=tuning, reference=reference, current=current, ctrl=ctrl,
                on_change=mark_dirty, mx=mx, my=my, panel=settings_rect,
            ):
                continue

            if race_bar_right.handle_event(
                ev, ctrl=ctrl, on_change=on_spec_change, mx=mx, my=my, rect=race_full_rect,
                tuning=tuning, on_tune=mark_dirty,
            ):
                continue

            if race_bar_left.handle_event(
                ev, ctrl=ctrl, on_change=on_spec_change, mx=mx, my=my, rect=race_compact_rect,
            ):
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_SPACE:
                    auto_walk = not auto_walk
                    if anim:
                        anim.set_walking(auto_walk)
                elif ev.key == pygame.K_r:
                    ctrl.seed = (ctrl.seed * 1103515245 + 12345) & 0x7FFFFFFF
                    mark_dirty()
                    renderer.reset_view()
                elif ev.key in (pygame.K_UP, pygame.K_w) and anim:
                    anim.set_facing("n")
                elif ev.key in (pygame.K_DOWN, pygame.K_s) and anim:
                    anim.set_facing("s")
                elif ev.key in (pygame.K_LEFT, pygame.K_a) and anim:
                    anim.set_facing("w")
                elif ev.key in (pygame.K_RIGHT, pygame.K_d) and anim:
                    anim.set_facing("e")
                elif ev.key == pygame.K_HOME:
                    renderer.reset_view()

            if mx >= left_panel.w:
                continue

            if ev.type == pygame.MOUSEWHEEL and anim:
                steps = _wheel_steps(ev)
                if steps:
                    renderer.orbit.zoom_wheel(steps)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 3:
                    drag_mode = "orbit"
                elif ev.button in (1, 2):
                    drag_mode = "pan"
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button in (1, 2, 3):
                    drag_mode = None
            elif ev.type == pygame.MOUSEMOTION and drag_mode:
                if drag_mode == "orbit" and ev.buttons[2]:
                    renderer.orbit.rotate_drag(ev.rel[0], ev.rel[1])
                elif drag_mode == "pan" and (ev.buttons[0] or ev.buttons[1]):
                    renderer.orbit.pan_pixels(ev.rel[0], ev.rel[1])

        screen.fill((10, 12, 18))

        if anim and pose_set:
            model = anim.current_model()
            race = load_race(ctrl.race_id)
            hud = [
                f"{race.display_name} seed={ctrl.seed} overrides={len(tuning.locked)}",
                f"facing={anim.facing} {'WALK' if auto_walk else 'IDLE'} phase={anim.walk_phase()}",
                f"{_orbit_label(renderer)}  RMB orbit  Space walk",
            ]
            view_h = left_panel.h - race_compact_rect.h
            preview = renderer.render(
                model,
                title=f"Tuner preview — {race.display_name}",
                hud_lines=hud,
            )
            if rebuilding:
                overlay = pygame.Surface(preview.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                preview.blit(overlay, (0, 0))
                preview.blit(font.render("rebuilding…", True, (255, 220, 120)), (12, 40))
            title_h = renderer._font_hud.get_height() + 6
            draw_limb_legend(preview, y=8 + title_h, font=renderer._font_hud)
            screen.blit(preview, (0, race_compact_rect.h), (0, 0, TUNER_LEFT_W, view_h))

        race_bar_left.draw(screen, ctrl=ctrl, rect=race_compact_rect, font=font, small=small)
        race_bar_right.draw(screen, ctrl=ctrl, rect=race_full_rect, font=font, small=small, tuning=tuning)
        settings.draw(
            screen, tuning=tuning, reference=reference, current=current, ctrl=ctrl,
            panel=settings_rect, font=font, small=small, mono=mono,
            rebuilding=rebuilding, on_export=do_export,
        )

        pygame.draw.line(screen, (55, 60, 80), (TUNER_LEFT_W, 0), (TUNER_LEFT_W, TUNER_WINDOW_PX_H), 2)
        pygame.display.flip()
        time.sleep(1.0 / 60)

    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Character generator live tuner")
    parser.add_argument("--race", default="human")
    parser.add_argument("--age", type=float, default=28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sex", default="neutral", choices=["male", "female", "neutral"])
    parser.add_argument("--age-preset", default="", choices=["", "child", "young", "adult", "elder"])
    parser.add_argument("--no-walk", action="store_true")
    args = parser.parse_args()
    init_paths(ROOT)
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
