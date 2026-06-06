#!/usr/bin/env python3
"""Character + animation editor with iso-stencil preview and voxel paint.

See docs/CHARACTER_EDITOR.md for full documentation.

Run:
  python scripts/character_editor.py
  python scripts/character_editor.py --race dwarf --age 50 --seed 7
"""
from __future__ import annotations

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

from src.characters.anim import AnimPlayer
from src.characters.bake import bake_pose_set
from src.characters.editor_anim_bar import EditorAnimBar
from src.characters.editor_mode_bar import EditorModeBar
from src.characters.editor_parts_tree import EditorPartsTree
from src.characters.editor_state import EditorState
from src.characters.editor_voxel_tools import (
    arrow_delta,
    create_voxel,
    default_create_pos,
    delete_voxel,
    move_voxel_in_edits,
    rotate_facing,
    voxel_at,
)
from src.characters.loader import load_race
from src.characters.morphology import LifeStage
from src.characters.tuning import (
    SpecController,
    TuningState,
    build_current_values,
    build_reference,
    stage_preset_age,
)
from src.characters.tuner_ui import RaceAgeBar, Rect, SettingsPanel, export_to_files
from src.characters.voxel_edits import save_voxel_edits
from src.constants import init_paths
from src.prototype.dia_scale.display_scale import (
    EDITOR_ANIM_H,
    EDITOR_PARAMS_W,
    EDITOR_PARTS_W,
    EDITOR_VIEW_H,
    EDITOR_VIEW_W,
    EDITOR_WINDOW_PX_H,
    EDITOR_WINDOW_PX_W,
    PRESET_NORMAL,
)
from src.prototype.dia_scale.iso_character_renderer import IsoCharacterRenderer

DEBOUNCE_S = 0.15
MODE_BAR_H = 22


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
    editor = EditorState()
    reference = build_reference(ctrl.to_spec())
    current = build_current_values(ctrl.to_spec(), tuning)

    dirty = True
    last_change = 0.0
    rebuilding = False
    pose_set = bake_pose_set(ctrl.to_spec(), tuning=tuning, edits=editor.voxel_edits)
    walk_period = float(tuning.get("anim.walk_period_s", 0.36))
    anim = AnimPlayer(pose_set, walk_period_s=walk_period)
    anim.set_walking(True)
    dirty = False
    last_render = None

    renderer = IsoCharacterRenderer(
        preset=PRESET_NORMAL,
        panel_w=EDITOR_VIEW_W,
        panel_h=EDITOR_VIEW_H,
        hud_font_size=11,
    )

    parts_tree = EditorPartsTree()
    anim_bar = EditorAnimBar()
    mode_bar = EditorModeBar()
    race_bar = RaceAgeBar(compact=False)
    settings = SettingsPanel()

    font = pygame.font.SysFont("segoe ui", 13)
    small = pygame.font.SysFont("segoe ui", 11)
    mono = pygame.font.SysFont("consolas", 10)

    screen = pygame.display.set_mode((EDITOR_WINDOW_PX_W, EDITOR_WINDOW_PX_H))
    pygame.display.set_caption("character_editor [generator]")

    parts_rect = Rect(0, 0, EDITOR_PARTS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    view_rect = Rect(EDITOR_PARTS_W, 0, EDITOR_VIEW_W, EDITOR_VIEW_H)
    params_rect = Rect(EDITOR_PARTS_W + EDITOR_VIEW_W, 0, EDITOR_PARAMS_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H)
    mode_rect = Rect(params_rect.x, 0, EDITOR_PARAMS_W, MODE_BAR_H)
    race_rect = Rect(params_rect.x, MODE_BAR_H, EDITOR_PARAMS_W, race_bar.height)
    settings_rect = Rect(
        params_rect.x, MODE_BAR_H + race_bar.height, EDITOR_PARAMS_W,
        params_rect.h - race_bar.height - MODE_BAR_H,
    )
    anim_rect = Rect(0, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H, EDITOR_WINDOW_PX_W, EDITOR_ANIM_H)

    running = True

    def mark_dirty(*, rebuild_edits: bool = False) -> None:
        nonlocal dirty, last_change, reference, current, pose_set
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
        if rebuild_edits:
            pose_set.edits = editor.voxel_edits
            pose_set.invalidate_cache()

    def on_spec_change() -> None:
        tuning.reset_prefix("race.")
        mark_dirty()

    def toggle_mode() -> None:
        editor.toggle_mode()
        pygame.display.set_caption(f"character_editor [{editor.mode}]")

    def set_mode(mode: str) -> None:
        editor.set_mode(mode)  # type: ignore[arg-type]
        pygame.display.set_caption(f"character_editor [{editor.mode}]")

    def do_export(_tuning: TuningState, ref: dict, _ctrl: SpecController) -> None:
        export_dir = os.path.join(ROOT, "exports")
        os.makedirs(export_dir, exist_ok=True)
        jp, tp = export_to_files(_tuning, ref, _ctrl, export_dir=export_dir)
        print(f"Exported: {jp}\n         {tp}")
        if editor.mode == "character":
            ep = os.path.join(export_dir, "voxel_edits.json")
            save_voxel_edits(ep, editor.voxel_edits)
            print(f"         {ep}")

    def settings_readonly() -> bool:
        return editor.mode == "character"

    while running:
        now = time.monotonic()
        if dirty and now - last_change >= DEBOUNCE_S:
            rebuilding = True
            spec = ctrl.to_spec()
            walk_period = float(tuning.get("anim.walk_period_s", 0.36))
            pose_set = bake_pose_set(spec, tuning=tuning, edits=editor.voxel_edits)
            anim.pose_set = pose_set
            anim.walk_period_s = walk_period
            current = build_current_values(spec, tuning)
            dirty = False
            rebuilding = False

        mx, my = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                continue

            if mode_bar.handle_event(
                ev, mode=editor.mode, on_toggle=toggle_mode, on_set=set_mode, mx=mx, my=my, rect=mode_rect,
            ):
                continue

            if anim_bar.handle_event(ev, anim=anim, on_change=lambda: None, mx=mx, my=my, rect=anim_rect):
                continue

            if parts_tree.handle_event(
                ev, state=editor, on_change=lambda: mark_dirty(rebuild_edits=True), mx=mx, my=my, rect=parts_rect,
            ):
                continue

            if not settings_readonly() and settings.handle_event(
                ev, tuning=tuning, reference=reference, current=current, ctrl=ctrl,
                on_change=mark_dirty, mx=mx, my=my, panel=settings_rect,
            ):
                continue

            if race_bar.handle_event(
                ev, ctrl=ctrl, on_change=on_spec_change, mx=mx, my=my, rect=race_rect,
                tuning=tuning, on_tune=mark_dirty,
            ):
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    editor.deselect()
                elif ev.key == pygame.K_SPACE:
                    anim.toggle_pause()
                elif ev.key == pygame.K_m:
                    toggle_mode()
                elif ev.key == pygame.K_z:
                    anim.set_facing(rotate_facing(anim.facing, -1))
                elif ev.key == pygame.K_x:
                    anim.set_facing(rotate_facing(anim.facing, 1))
                elif ev.key == pygame.K_a:
                    anim.set_manual_phase((anim.walk_phase() - 1) % 3)
                    anim.paused = True
                elif ev.key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    anim.set_manual_phase((anim.walk_phase() + 1) % 3)
                    anim.paused = True
                elif ev.key == pygame.K_r:
                    ctrl.seed = (ctrl.seed * 1103515245 + 12345) & 0x7FFFFFFF
                    mark_dirty()
                else:
                    delta = arrow_delta(ev.key, anim.facing)
                    if delta and editor.selected_voxel and last_render is not None:
                        model = anim.current_model()
                        ox, oy, oz = editor.selected_voxel
                        dx, dy, dz = delta
                        new_pos = (ox + dx, oy + dy, oz + dz)
                        if move_voxel_in_edits(editor.voxel_edits, model, editor.selected_voxel, new_pos):
                            editor.select_voxel(new_pos)
                            mark_dirty(rebuild_edits=True)

            if view_rect.collide(mx, my) and ev.type == pygame.MOUSEBUTTONDOWN:
                if last_render and not rebuilding:
                    model = anim.current_model()
                    vx = mx - view_rect.x
                    vy = my - view_rect.y
                    if ev.button == 1:
                        pick = renderer.pick_voxel(
                            model, vx, vy, last_render,
                            kind_filter=editor.kind_filter(),
                            hidden_kinds=editor.hidden_kinds(),
                        )
                        if pick:
                            kind = voxel_at(model, editor.voxel_edits, pick)
                            editor.select_voxel(pick, kind or editor.selected_kind)
                        else:
                            pos = default_create_pos(
                                model, editor.voxel_edits,
                                selected=editor.selected_voxel,
                                anchor_x=model.anchor_x,
                                anchor_y=model.anchor_y,
                            )
                            create_voxel(editor.voxel_edits, pos, editor.selected_kind)
                            editor.select_voxel(pos, editor.selected_kind)
                            mark_dirty(rebuild_edits=True)
                    elif ev.button == 3:
                        pick = renderer.pick_voxel(
                            model, vx, vy, last_render,
                            kind_filter=editor.kind_filter(),
                            hidden_kinds=editor.hidden_kinds(),
                        )
                        if pick:
                            delete_voxel(editor.voxel_edits, model, pick)
                            if editor.selected_voxel == pick:
                                editor.deselect()
                            mark_dirty(rebuild_edits=True)
                    continue

        screen.fill((10, 12, 18))

        model = anim.current_model()
        race = load_race(ctrl.race_id)
        from src.characters.editor_diagnostics import analyze_voxels

        diag = analyze_voxels(model.voxels, walking=anim.walking).summary()
        hud = [
            f"[{editor.mode}] {race.display_name} seed={ctrl.seed} facing={anim.facing} "
            f"{'PAUSED' if anim.paused else 'PLAY'} phase={anim.walk_phase()}",
            "Z/X=facing A/S=frame arrows=move | docs/CHARACTER_EDITOR.md",
            diag,
        ]
        view_surf = renderer.render(
            model,
            title="Iso stencil preview",
            hud_lines=hud,
            kind_filter=editor.kind_filter(),
            hidden_kinds=editor.hidden_kinds(),
            highlight_kind=editor.selected_kind,
            highlight_voxel=editor.selected_voxel,
            walking=anim.walking,
        )
        last_render = view_surf
        if rebuilding:
            overlay = pygame.Surface(view_surf.surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            view_surf.surface.blit(overlay, (0, 0))
            view_surf.surface.blit(font.render("rebuilding…", True, (255, 220, 120)), (12, 40))
        screen.blit(view_surf.surface, (view_rect.x, view_rect.y))

        parts_tree.draw(screen, state=editor, rect=parts_rect, font=font, small=small)
        mode_bar.draw(screen, mode=editor.mode, rect=mode_rect, small=small)
        race_bar.draw(screen, ctrl=ctrl, rect=race_rect, font=font, small=small, tuning=tuning)
        if not settings_readonly():
            settings.draw(
                screen, tuning=tuning, reference=reference, current=current, ctrl=ctrl,
                panel=settings_rect, font=font, small=small, mono=mono,
                rebuilding=rebuilding, on_export=do_export,
            )
        else:
            pygame.draw.rect(screen, (22, 26, 38), (settings_rect.x, settings_rect.y, settings_rect.w, settings_rect.h))
            screen.blit(
                small.render("Character mode — generator params hidden", True, (140, 145, 160)),
                (settings_rect.x + 8, settings_rect.y + 8),
            )
            screen.blit(
                small.render("Export saves voxel_edits.json", True, (100, 105, 120)),
                (settings_rect.x + 8, settings_rect.y + 28),
            )
        anim_bar.draw(screen, anim=anim, rect=anim_rect, font=font, small=small)

        pygame.draw.line(screen, (55, 60, 80), (EDITOR_PARTS_W, 0), (EDITOR_PARTS_W, EDITOR_WINDOW_PX_H), 1)
        pygame.draw.line(
            screen, (55, 60, 80),
            (EDITOR_PARTS_W + EDITOR_VIEW_W, 0),
            (EDITOR_PARTS_W + EDITOR_VIEW_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H),
            1,
        )
        pygame.draw.line(
            screen, (55, 60, 80),
            (0, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H),
            (EDITOR_WINDOW_PX_W, EDITOR_WINDOW_PX_H - EDITOR_ANIM_H),
            1,
        )
        pygame.display.flip()
        time.sleep(1.0 / 60)

    pygame.quit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Character + animation editor")
    parser.add_argument("--race", default="human")
    parser.add_argument("--age", type=float, default=28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sex", default="neutral", choices=["male", "female", "neutral"])
    parser.add_argument("--age-preset", default="", choices=["", "child", "young", "adult", "elder"])
    args = parser.parse_args()
    init_paths(ROOT)
    return run_interactive(args)


if __name__ == "__main__":
    raise SystemExit(main())
