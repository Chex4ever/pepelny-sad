"""Pygame UI for character generator tuning panel."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

import pygame

from src.characters.lifecycle import resolve_life_stage
from src.characters.loader import load_race, load_races_catalog
from src.characters.morphology import LifeStage
from src.characters.param_registry import GROUP_ORDER, PARAM_BY_PATH, ParamDef, params_by_group
from src.characters.tuning import (
    SpecController,
    TuningState,
    build_reference,
    life_stage_label,
    stage_preset_age,
)

COLOR_BG = (14, 16, 24)
COLOR_PANEL = (22, 26, 38)
COLOR_BORDER = (55, 60, 80)
COLOR_TEXT = (200, 205, 220)
COLOR_DIM = (120, 125, 145)
COLOR_ACCENT = (100, 160, 255)
COLOR_OVERRIDE = (255, 200, 80)
COLOR_BTN = (40, 44, 58)
COLOR_BTN_HOVER = (55, 62, 82)
COLOR_BTN_ACTIVE = (70, 90, 130)
ROW_H = 24
GROUP_H = 26
RACE_BAR_FULL_H = 142
RACE_BAR_COMPACT_H = 28
TOP_TOOL_H = 32
PROP_SCALE_MIN = 0.5
PROP_SCALE_MAX = 1.5
SLIDER_HIT_PAD = 6
COL_PATH_W = 168
COL_BTN_W = 26
COL_VAL_W = 88
COL_GAP = 3


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    def collide(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


@dataclass
class HitTarget:
    kind: str
    rect: Rect
    path: str = ""
    meta: Any = None


def _fmt_val(val: Any, kind: str) -> str:
    if val is None:
        return "—"
    if kind == "readonly":
        return str(val)
    if kind == "int":
        return str(int(round(float(val))))
    if kind == "float":
        return f"{float(val):.4g}"
    return str(val)


def _clamp_param(val: float, pdef: ParamDef) -> float:
    if pdef.min is not None:
        val = max(pdef.min, val)
    if pdef.max is not None:
        val = min(pdef.max, val)
    return val


def _draw_btn(surf: pygame.Surface, rect: Rect, label: str, font: pygame.font.Font, *, active: bool = False) -> None:
    bg = COLOR_BTN_ACTIVE if active else COLOR_BTN
    pygame.draw.rect(surf, bg, (rect.x, rect.y, rect.w, rect.h), border_radius=3)
    pygame.draw.rect(surf, COLOR_BORDER, (rect.x, rect.y, rect.w, rect.h), 1, border_radius=3)
    ts = font.render(label, True, COLOR_TEXT)
    surf.blit(ts, (rect.x + (rect.w - ts.get_width()) // 2, rect.y + (rect.h - ts.get_height()) // 2))


class RaceAgeBar:
    """Race grid + age controls."""

    STAGE_LABELS = ("Ребёнок", "Юный", "Взрослый", "Старик")
    STAGES = (LifeStage.CHILD, LifeStage.YOUNG, LifeStage.ADULT, LifeStage.ELDER)

    def __init__(self, *, compact: bool = False) -> None:
        self.compact = compact
        self.race_ids = sorted(load_races_catalog().keys())
        self._hits: list[HitTarget] = []
        self._slider_drag = False
        self._prop_drag = False
        self._slider_rect: Rect | None = None
        self._prop_slider_rect: Rect | None = None
        self.show_race_popup = False

    @property
    def height(self) -> int:
        return RACE_BAR_COMPACT_H if self.compact else RACE_BAR_FULL_H

    def _race_display(self, race_id: str) -> str:
        return load_races_catalog()[race_id].display_name

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        ctrl: SpecController,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        rect: Rect,
        tuning: TuningState | None = None,
        on_tune: Callable[[], None] | None = None,
    ) -> bool:
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            if self._slider_drag or self._prop_drag:
                self._slider_drag = False
                self._prop_drag = False
                return True

        if ev.type == pygame.MOUSEMOTION:
            if self._slider_drag and self._slider_rect:
                self._apply_slider(mx, ctrl, on_change, self._slider_rect)
                return True
            if self._prop_drag and self._prop_slider_rect and tuning is not None and on_tune is not None:
                self._apply_prop_slider(mx, tuning, on_tune, self._prop_slider_rect)
                return True

        if not rect.collide(mx, my) and ev.type != pygame.KEYDOWN:
            if self.show_race_popup and ev.type == pygame.MOUSEBUTTONUP:
                self.show_race_popup = False
            return False

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_TAB:
                mods = pygame.key.get_mods()
                idx = self.race_ids.index(ctrl.race_id) if ctrl.race_id in self.race_ids else 0
                if mods & pygame.KMOD_SHIFT:
                    idx = (idx - 1) % len(self.race_ids)
                else:
                    idx = (idx + 1) % len(self.race_ids)
                self._set_race(ctrl, self.race_ids[idx], on_change)
                return True
            if ev.key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
                delta = -5 if ev.key == pygame.K_LEFTBRACKET else 5
                self._set_age(ctrl, ctrl.age_years + delta, on_change)
                return True
            if ev.key in (pygame.K_COMMA, pygame.K_PERIOD):
                delta = -1 if ev.key == pygame.K_COMMA else 1
                self._set_age(ctrl, ctrl.age_years + delta, on_change)
                return True
            if pygame.K_1 <= ev.key <= pygame.K_8:
                i = ev.key - pygame.K_1
                if i < len(self.race_ids):
                    self._set_race(ctrl, self.race_ids[i], on_change)
                return True

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for hit in self._hits:
                if not hit.rect.collide(mx, my):
                    continue
                if hit.kind == "race":
                    self._set_race(ctrl, hit.meta, on_change)
                    self.show_race_popup = False
                    return True
                if hit.kind == "stage":
                    race = load_race(ctrl.race_id)
                    age = stage_preset_age(race, hit.meta)
                    self._set_age(ctrl, age, on_change)
                    return True
                if hit.kind == "age_minus":
                    self._set_age(ctrl, ctrl.age_years - (5 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1), on_change)
                    return True
                if hit.kind == "age_plus":
                    self._set_age(ctrl, ctrl.age_years + (5 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1), on_change)
                    return True
                if hit.kind == "race_prev":
                    idx = self.race_ids.index(ctrl.race_id)
                    self._set_race(ctrl, self.race_ids[(idx - 1) % len(self.race_ids)], on_change)
                    return True
                if hit.kind == "race_next":
                    idx = self.race_ids.index(ctrl.race_id)
                    self._set_race(ctrl, self.race_ids[(idx + 1) % len(self.race_ids)], on_change)
                    return True
                if hit.kind == "race_popup":
                    self.show_race_popup = not self.show_race_popup
                    return True
                if hit.kind == "slider":
                    self._slider_drag = True
                    self._apply_slider(mx, ctrl, on_change, hit.rect)
                    return True
                if hit.kind == "prop_slider" and tuning is not None and on_tune is not None:
                    self._prop_drag = True
                    self._apply_prop_slider(mx, tuning, on_tune, hit.rect)
                    return True
            if self.show_race_popup:
                self.show_race_popup = False

        return rect.collide(mx, my)

    def _set_race(self, ctrl: SpecController, race_id: str, on_change: Callable[[], None]) -> None:
        ctrl.race_id = race_id
        ctrl.clamp_age_to_race()
        on_change()

    def _set_age(self, ctrl: SpecController, age: float, on_change: Callable[[], None]) -> None:
        race = load_race(ctrl.race_id)
        ctrl.age_years = max(1.0, min(float(race.max_age_years), age))
        on_change()

    def _apply_slider(self, mx: int, ctrl: SpecController, on_change: Callable[[], None], rect: Rect) -> None:
        race = load_race(ctrl.race_id)
        t = max(0.0, min(1.0, (mx - rect.x) / max(1, rect.w)))
        age = 1.0 + t * (race.max_age_years - 1)
        ctrl.age_years = age
        on_change()

    def _apply_prop_slider(
        self, mx: int, tuning: TuningState, on_change: Callable[[], None], rect: Rect,
    ) -> None:
        t = max(0.0, min(1.0, (mx - rect.x) / max(1, rect.w)))
        scale = PROP_SCALE_MIN + t * (PROP_SCALE_MAX - PROP_SCALE_MIN)
        if abs(tuning.proportion_scale - scale) > 1e-4:
            tuning.proportion_scale = scale
            on_change()

    def draw(
        self,
        surf: pygame.Surface,
        *,
        ctrl: SpecController,
        rect: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
        tuning: TuningState | None = None,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_PANEL, (rect.x, rect.y, rect.w, rect.h))
        pygame.draw.rect(surf, COLOR_BORDER, (rect.x, rect.y, rect.w, rect.h), 1)
        race = load_race(ctrl.race_id)
        stage = resolve_life_stage(ctrl.age_years, race)
        stage_ru = life_stage_label(stage)

        if self.compact:
            y = rect.y + 4
            label = f"{race.display_name} ({ctrl.race_id}) · {ctrl.age_years:.0f} лет · {stage_ru}"
            lbl_s = font.render(label, True, COLOR_TEXT)
            lbl_r = Rect(rect.x + 6, y, lbl_s.get_width() + 4, RACE_BAR_COMPACT_H - 8)
            surf.blit(lbl_s, (lbl_r.x, y))
            self._hits.append(HitTarget("race_popup", lbl_r))

            bx = rect.x + rect.w - 130
            for kind, dx, label in (
                ("race_prev", 0, "<"),
                ("age_minus", 28, "-"),
                ("age_plus", 56, "+"),
                ("race_next", 84, ">"),
            ):
                r = Rect(bx + dx, y, COL_BTN_W, RACE_BAR_COMPACT_H - 10)
                _draw_btn(surf, r, label, small)
                self._hits.append(HitTarget(kind, r))
            return

        y = rect.y + 4
        surf.blit(font.render("Раса", True, COLOR_DIM), (rect.x + 6, y))
        y += 18
        cols, btn_w, btn_h = 4, (rect.w - 16) // 4 - 2, 22
        for i, rid in enumerate(self.race_ids):
            col, row = i % cols, i // cols
            bx = rect.x + 6 + col * (btn_w + 2)
            by = y + row * (btn_h + 2)
            r = Rect(bx, by, btn_w, btn_h)
            active = rid == ctrl.race_id
            pygame.draw.rect(surf, COLOR_BTN_ACTIVE if active else COLOR_BTN, (r.x, r.y, r.w, r.h), border_radius=2)
            name = load_races_catalog()[rid].display_name
            surf.blit(small.render(name[:8], True, COLOR_TEXT), (r.x + 3, r.y + 2))
            surf.blit(small.render(rid[:6], True, COLOR_DIM), (r.x + 3, r.y + 11))
            self._hits.append(HitTarget("race", r, meta=rid))

        ay = rect.y + 58
        surf.blit(font.render("Возраст", True, COLOR_DIM), (rect.x + 6, ay))
        badge = small.render(stage_ru, True, COLOR_ACCENT)
        surf.blit(badge, (rect.x + 80, ay))

        py = ay + 18
        for i, (lbl, st) in enumerate(zip(self.STAGE_LABELS, self.STAGES)):
            r = Rect(rect.x + 6 + i * 72, py, 68, 20)
            pygame.draw.rect(surf, COLOR_BTN, (r.x, r.y, r.w, r.h), border_radius=2)
            surf.blit(small.render(lbl, True, COLOR_TEXT), (r.x + 4, r.y + 3))
            self._hits.append(HitTarget("stage", r, meta=st))

        sy = py + 26
        slider_vis = Rect(rect.x + 6, sy, rect.w - 12, 10)
        self._slider_rect = slider_vis
        pygame.draw.rect(surf, (30, 34, 48), (slider_vis.x, slider_vis.y, slider_vis.w, slider_vis.h), border_radius=3)
        t = (ctrl.age_years - 1) / max(1, race.max_age_years - 1)
        knob_x = slider_vis.x + int(t * slider_vis.w)
        pygame.draw.rect(surf, COLOR_ACCENT, (knob_x - 3, slider_vis.y - 1, 6, slider_vis.h + 2), border_radius=2)
        slider_hit = Rect(slider_vis.x, slider_vis.y - SLIDER_HIT_PAD, slider_vis.w, slider_vis.h + SLIDER_HIT_PAD * 2)
        self._hits.append(HitTarget("slider", slider_hit))
        age_txt = font.render(f"{ctrl.age_years:.0f} лет", True, COLOR_TEXT)
        surf.blit(age_txt, (rect.x + 6, sy + 14))

        age_btn_y = sy + 12
        r_minus = Rect(rect.x + rect.w - 64, age_btn_y, COL_BTN_W, 22)
        r_plus = Rect(rect.x + rect.w - 32, age_btn_y, COL_BTN_W, 22)
        _draw_btn(surf, r_minus, "-", small)
        _draw_btn(surf, r_plus, "+", small)
        self._hits.append(HitTarget("age_minus", r_minus))
        self._hits.append(HitTarget("age_plus", r_plus))

        if tuning is not None:
            pry = sy + 34
            scale = tuning.proportion_scale
            scaled = abs(scale - 1.0) > 1e-4
            surf.blit(font.render("Пропорции", True, COLOR_DIM), (rect.x + 6, pry))
            scale_lbl = small.render(f"×{scale:.2f}", True, COLOR_OVERRIDE if scaled else COLOR_TEXT)
            surf.blit(scale_lbl, (rect.x + 88, pry + 1))
            prop_vis = Rect(rect.x + 130, pry + 4, rect.w - 142, 10)
            self._prop_slider_rect = prop_vis
            pygame.draw.rect(surf, (30, 34, 48), (prop_vis.x, prop_vis.y, prop_vis.w, prop_vis.h), border_radius=3)
            pt = (scale - PROP_SCALE_MIN) / (PROP_SCALE_MAX - PROP_SCALE_MIN)
            pknob = prop_vis.x + int(max(0.0, min(1.0, pt)) * prop_vis.w)
            pygame.draw.rect(surf, COLOR_OVERRIDE if scaled else COLOR_ACCENT, (pknob - 3, prop_vis.y - 1, 6, prop_vis.h + 2), border_radius=2)
            prop_hit = Rect(prop_vis.x, prop_vis.y - SLIDER_HIT_PAD, prop_vis.w, prop_vis.h + SLIDER_HIT_PAD * 2)
            self._hits.append(HitTarget("prop_slider", prop_hit))
            surf.blit(small.render(f"{PROP_SCALE_MIN:.1f}", True, COLOR_DIM), (prop_vis.x, pry + 16))
            surf.blit(
                small.render(f"{PROP_SCALE_MAX:.1f}", True, COLOR_DIM),
                (prop_vis.x + prop_vis.w - 18, pry + 16),
            )

        if self.show_race_popup:
            self._draw_race_popup(surf, rect, small, ctrl)

    def _draw_race_popup(self, surf: pygame.Surface, rect: Rect, small: pygame.font.Font, ctrl: SpecController) -> None:
        pop = pygame.Surface((200, 120), pygame.SRCALPHA)
        pop.fill((20, 22, 32, 240))
        for i, rid in enumerate(self.race_ids[:8]):
            r = Rect(4 + (i % 2) * 96, 4 + (i // 2) * 28, 92, 24)
            pygame.draw.rect(pop, COLOR_BTN_ACTIVE if rid == ctrl.race_id else COLOR_BTN, (r.x, r.y, r.w, r.h))
            pop.blit(small.render(rid, True, COLOR_TEXT), (r.x + 4, r.y + 5))
        surf.blit(pop, (rect.x + 8, rect.y + self.height))


@dataclass
class SettingsPanel:
    scroll_y: float = 0.0
    collapsed: dict[str, bool] = field(default_factory=dict)
    edit_path: str | None = None
    edit_buffer: str = ""
    _hits: list[HitTarget] = field(default_factory=list)
    _content_h: int = 0

    def __post_init__(self) -> None:
        for g in GROUP_ORDER:
            self.collapsed.setdefault(g, g in ("Joints", "Generate"))

    def content_height(self) -> int:
        return self._content_h

    def handle_event(
        self,
        ev: pygame.event.Event,
        *,
        tuning: TuningState,
        reference: dict[str, Any],
        current: dict[str, Any],
        ctrl: SpecController,
        on_change: Callable[[], None],
        mx: int,
        my: int,
        panel: Rect,
    ) -> bool:
        if self.edit_path and ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                self._commit_edit(tuning, reference, on_change)
                return True
            if ev.key == pygame.K_ESCAPE:
                self.edit_path = None
                return True
            if ev.key == pygame.K_BACKSPACE:
                self.edit_buffer = self.edit_buffer[:-1]
                return True
            if ev.unicode and ev.unicode.isprintable():
                self.edit_buffer += ev.unicode
                return True

        if ev.type == pygame.MOUSEWHEEL:
            if panel.collide(mx, my):
                self.scroll_y = max(0, self.scroll_y - ev.y * 24)
                return True

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for hit in self._hits:
                if not hit.rect.collide(mx, my):
                    continue
                if hit.kind == "group":
                    self.collapsed[hit.path] = not self.collapsed.get(hit.path, False)
                    return True
                if hit.kind == "minus":
                    self._nudge(tuning, hit.path, -1, reference, on_change)
                    return True
                if hit.kind == "plus":
                    self._nudge(tuning, hit.path, 1, reference, on_change)
                    return True
                if hit.kind == "value":
                    self.edit_path = hit.path
                    pdef = PARAM_BY_PATH.get(hit.path)
                    val = current.get(hit.path, reference.get(hit.path))
                    self.edit_buffer = _fmt_val(val, pdef.kind if pdef else "float")
                    return True
                if hit.kind == "ref":
                    ref = reference.get(hit.path)
                    if ref is not None:
                        tuning.set(hit.path, ref)
                        on_change()
                    return True
                if hit.kind == "reset_all":
                    tuning.reset_all()
                    on_change()
                    return True
                if hit.kind == "export":
                    hit.meta(tuning, reference, ctrl)
                    return True
            return panel.collide(mx, my)

        return False

    def _commit_edit(self, tuning: TuningState, reference: dict, on_change: Callable[[], None]) -> None:
        if not self.edit_path:
            return
        pdef = PARAM_BY_PATH.get(self.edit_path)
        if not pdef or pdef.kind == "readonly":
            self.edit_path = None
            return
        raw = self.edit_buffer.strip()
        try:
            if pdef.kind == "int":
                val = int(float(raw))
            elif pdef.kind == "float":
                val = float(raw)
            elif pdef.kind == "enum":
                val = raw
            else:
                val = raw
            if pdef.kind in ("int", "float"):
                val = _clamp_param(float(val), pdef)
                if pdef.kind == "int":
                    val = int(val)
            tuning.set(self.edit_path, val)
            on_change()
        except ValueError:
            pass
        self.edit_path = None

    def _nudge(self, tuning: TuningState, path: str, direction: int, reference: dict, on_change: Callable[[], None]) -> None:
        pdef = PARAM_BY_PATH.get(path)
        if not pdef or pdef.kind == "readonly":
            return
        base = tuning.get(path, reference.get(path, 0))
        try:
            if pdef.kind == "enum" and pdef.enum_values:
                vals = pdef.enum_values
                cur = str(base) if base in vals else vals[0]
                idx = (vals.index(cur) + direction) % len(vals)
                tuning.set(path, vals[idx])
            elif pdef.kind == "int":
                tuning.set(path, int(_clamp_param(int(base) + direction * int(pdef.step), pdef)))
            elif pdef.kind == "float":
                tuning.set(path, _clamp_param(float(base) + direction * pdef.step, pdef))
            else:
                return
            on_change()
        except (TypeError, ValueError):
            pass

    def draw(
        self,
        surf: pygame.Surface,
        *,
        tuning: TuningState,
        reference: dict[str, Any],
        current: dict[str, Any],
        ctrl: SpecController,
        panel: Rect,
        font: pygame.font.Font,
        small: pygame.font.Font,
        mono: pygame.font.Font,
        rebuilding: bool,
        on_export: Callable,
    ) -> None:
        self._hits.clear()
        pygame.draw.rect(surf, COLOR_BG, (panel.x, panel.y, panel.w, panel.h))
        pygame.draw.line(surf, COLOR_BORDER, (panel.x, panel.y), (panel.x, panel.y + panel.h))

        ty = panel.y + 4
        for label, kind in (("Reset all", "reset_all"), ("Export", "export")):
            r = Rect(panel.x + panel.w - (110 if kind == "reset_all" else 52), ty, 48 if kind == "export" else 52, 22)
            pygame.draw.rect(surf, COLOR_BTN, (r.x, r.y, r.w, r.h), border_radius=2)
            surf.blit(small.render(label, True, COLOR_TEXT), (r.x + 4, r.y + 4))
            self._hits.append(HitTarget(kind, r, meta=on_export if kind == "export" else None))

        if rebuilding:
            surf.blit(small.render("rebuilding…", True, COLOR_OVERRIDE), (panel.x + 8, ty + 4))

        ty += TOP_TOOL_H
        cy = ty - int(self.scroll_y)
        self._content_h = TOP_TOOL_H

        grouped = params_by_group()
        for group in GROUP_ORDER:
            params = grouped.get(group, [])
            if not params:
                continue
            if cy + GROUP_H >= panel.y and cy <= panel.y + panel.h:
                gr = Rect(panel.x + 4, cy, panel.w - 8, GROUP_H)
                pygame.draw.rect(surf, (28, 32, 46), (gr.x, gr.y, gr.w, gr.h), border_radius=2)
                arrow = "▸" if self.collapsed.get(group) else "▾"
                surf.blit(font.render(f"{arrow} {group}", True, COLOR_ACCENT), (gr.x + 6, gr.y + 4))
                self._hits.append(HitTarget("group", gr, path=group))
            cy += GROUP_H
            self._content_h += GROUP_H

            if self.collapsed.get(group):
                continue

            for pdef in params:
                if cy + ROW_H < panel.y or cy > panel.y + panel.h:
                    cy += ROW_H
                    self._content_h += ROW_H
                    continue
                self._draw_row(
                    surf, pdef, tuning, reference, current,
                    panel.x + 4, cy, panel.w - 8, mono, small,
                )
                cy += ROW_H
                self._content_h += ROW_H

        max_scroll = max(0, self._content_h - panel.h + TOP_TOOL_H + 8)
        self.scroll_y = min(self.scroll_y, max_scroll)

    def _draw_row(
        self,
        surf: pygame.Surface,
        pdef: ParamDef,
        tuning: TuningState,
        reference: dict,
        current: dict,
        x: int,
        y: int,
        w: int,
        mono: pygame.font.Font,
        small: pygame.font.Font,
    ) -> None:
        path = pdef.path
        val = current.get(path, reference.get(path))
        ref = reference.get(path)
        locked = tuning.is_locked(path)
        readonly = pdef.kind == "readonly"
        path_color = COLOR_OVERRIDE if locked else COLOR_DIM
        surf.blit(mono.render(path[:24], True, path_color), (x, y + 4))

        vx = x + COL_PATH_W
        btn_y = y + 2
        btn_h = ROW_H - 4

        r_minus = Rect(vx, btn_y, COL_BTN_W, btn_h)
        val_x = vx + COL_BTN_W + COL_GAP
        val_r = Rect(val_x, btn_y, COL_VAL_W, btn_h)
        r_plus = Rect(val_x + COL_VAL_W + COL_GAP, btn_y, COL_BTN_W, btn_h)

        if not readonly:
            _draw_btn(surf, r_minus, "-", small)
            self._hits.append(HitTarget("minus", r_minus, path=path))

        txt = self.edit_buffer if self.edit_path == path else _fmt_val(val, pdef.kind)
        pygame.draw.rect(
            surf,
            (35, 40, 55) if locked else (28, 32, 42),
            (val_r.x, val_r.y, val_r.w, val_r.h),
            border_radius=3,
        )
        if locked:
            pygame.draw.rect(surf, COLOR_OVERRIDE, (val_r.x, val_r.y, val_r.w, val_r.h), 1, border_radius=3)
        ts = mono.render(txt[:12], True, COLOR_TEXT)
        surf.blit(ts, (val_r.x + 4, val_r.y + (val_r.h - ts.get_height()) // 2))
        if not readonly:
            self._hits.append(HitTarget("value", val_r, path=path))
            _draw_btn(surf, r_plus, "+", small)
            self._hits.append(HitTarget("plus", r_plus, path=path))
            ref_x = r_plus.x + r_plus.w + 8
        else:
            ref_x = val_r.x + val_r.w + 8
        ref_s = small.render(f"ref:{_fmt_val(ref, pdef.kind)}", True, COLOR_DIM)
        surf.blit(ref_s, (ref_x, y + 5))
        self._hits.append(HitTarget("ref", Rect(ref_x, y, 100, ROW_H), path=path))

        if pdef.description_ru:
            desc = pdef.description_ru[:28]
            desc_x = x + w - small.size(desc)[0] - 4
            if desc_x > ref_x + 110:
                surf.blit(small.render(desc, True, (90, 95, 110)), (desc_x, y + 5))


def export_to_files(tuning: TuningState, reference: dict, ctrl: SpecController, export_dir: str = "exports") -> tuple[str, str]:
    os.makedirs(export_dir, exist_ok=True)
    spec = ctrl.to_spec()
    json_path = os.path.join(export_dir, "tuning_overrides.json")
    txt_path = os.path.join(export_dir, "tuning_diff.txt")
    import json

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tuning.export_bundle(spec, reference), f, indent=2, ensure_ascii=False)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(tuning.export_diff_text(spec, reference))
        for p in sorted(tuning.locked):
            pdef = PARAM_BY_PATH.get(p)
            if pdef and pdef.export_hint:
                f.write(f"# {p} → {pdef.export_hint}\n")
    return json_path, txt_path
