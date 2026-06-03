"""Full Undertale-style battle scene."""
from __future__ import annotations

import pygame

from src.battle.bullets import BulletPattern, check_hit
from src.battle.enemy_portrait import draw_enemy_portrait
from src.battle.fight_qte import FightQTE
from src.battle.soul_scan import apply_scan_effect, mercy_available
from src.constants import (
    COLOR_HP,
    COLOR_HIGHLIGHT,
    COLOR_MERcy,
    COLOR_TEXT,
    COLOR_UI_BG,
    COLOR_UI_BORDER,
    SCREEN_H,
    SCREEN_W,
)
from src.data.art_loader import load_enemies, load_items
from src.render.screen_buffer import ScreenBuffer
from src.ui.examine_panel import ExaminePanel
from src.world.companions import spawn_companion
from src.world.dungeon_reskin import bullet_speed_mult


class BattleScene:
    PHASE_INTRO = "intro"
    PHASE_MENU = "menu"
    PHASE_ACT = "act"
    PHASE_ITEM = "item"
    PHASE_FIGHT = "fight"
    PHASE_DODGE = "dodge"
    PHASE_END = "end"

    MENU = ["Fight", "Act", "Item", "Mercy"]

    def __init__(self, enemy_id: str, profile, world_state, on_done, audio=None):
        self.enemy_id = enemy_id
        self.enemies = load_enemies()
        self.enemy = dict(self.enemies[enemy_id])
        self.enemy_hp = self.enemy["hp"]
        self.profile = profile
        self.world_state = world_state
        self.on_done = on_done
        self.audio = audio
        self.phase = self.PHASE_INTRO
        self.intro_timer = 90
        self.menu_cursor = 0
        self.act_cursor = 0
        self.item_cursor = 0
        self.scan_flags: set = set()
        self.log: list[str] = []
        self.result = None  # win kill, spare, lose
        self.examine = ExaminePanel()
        self.combat = profile.combat_profile()
        self.pattern_idx = 0
        self.pattern: BulletPattern | None = None
        self.soul_x = 20.0
        self.soul_y = 10.0
        self.box_w = 40.0 if self.combat.box_shape == "wide" else 28.0
        self.box_h = 16.0 if self.combat.box_shape == "wide" else 20.0
        self.qte = FightQTE(self.combat.fight_mode)
        self.dodge_timer = 0
        self.dodge_max = 180
        self.frame = 0
        self.reveal_tell = False
        if self.audio:
            self.audio.play_sfx("battle_start")

    def _log(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 8:
            self.log.pop(0)

    def update(self):
        self.frame += 1
        if self.phase == self.PHASE_INTRO:
            self.intro_timer -= 1
            if self.intro_timer <= 0:
                self.phase = self.PHASE_MENU
        elif self.phase == self.PHASE_FIGHT:
            self.qte.update()
        elif self.phase == self.PHASE_DODGE:
            self.dodge_timer += 1
            if self.pattern:
                self.pattern.update()
                if check_hit(self.soul_x, self.soul_y, 0.6, self.pattern.active_bullets()):
                    dmg = max(1, 4 - self.combat.armor // 2)
                    self.profile.hp -= dmg
                    self._log(f"Попадание! -{dmg} HP")
                    if self.audio:
                        self.audio.play_sfx("hit")
                    if self.profile.hp <= 0:
                        self.result = "lose"
                        self.phase = self.PHASE_END
                if self.pattern.done or self.dodge_timer >= self.dodge_max:
                    self.phase = self.PHASE_MENU
                    self.pattern = None
                    self.dodge_timer = 0

    def _start_dodge(self):
        patterns = self.enemy.get("patterns", ["rain"])
        pid = patterns[self.pattern_idx % len(patterns)]
        self.pattern_idx += 1
        speed = bullet_speed_mult(
            self.world_state.kill_count,
            self.world_state.spare_count,
            self.world_state.layer == "dungeon",
        )
        self.pattern = BulletPattern(pid, self.box_w, self.box_h, speed)
        self.reveal_tell = any(f"reveal_{pid}" in f for f in self.scan_flags)
        self.soul_x = self.box_w / 2
        self.soul_y = self.box_h / 2
        self.phase = self.PHASE_DODGE
        self.dodge_timer = 0

    def handle_input(self, inp):
        if self.examine.open:
            if inp.pressed_escape():
                self.examine.close()
            return
        if self.phase == self.PHASE_END:
            if inp.action_pressed() or inp.pressed_escape():
                self.on_done(self.result)
            return
        if self.phase == self.PHASE_INTRO:
            if inp.action_pressed():
                self.phase = self.PHASE_MENU
            return
        if self.phase == self.PHASE_DODGE:
            spd = 0.8
            if inp.nav_left_held():
                self.soul_x = max(1, self.soul_x - spd)
            if inp.nav_right_held():
                self.soul_x = min(self.box_w - 1, self.soul_x + spd)
            if inp.nav_up_held():
                self.soul_y = max(1, self.soul_y - spd)
            if inp.nav_down_held():
                self.soul_y = min(self.box_h - 1, self.soul_y + spd)
            return
        if self.phase == self.PHASE_FIGHT:
            if inp.action_pressed():
                if self.qte.try_hit():
                    dmg = self.combat.fight_damage
                    self.enemy_hp -= dmg
                    self._log(f"Удар! -{dmg}")
                    if self.enemy_hp <= 0:
                        self.result = "kill"
                        self.world_state.kill_count += 1
                        self._grant_drops()
                        self.phase = self.PHASE_END
                        return
                else:
                    self._log("Промах.")
                self._start_dodge()
            return

        if inp.pressed(pygame.K_o):
            self.examine.show(self.enemy.get("art_id", self.enemy_id))
            return

        if inp.mouse_left_clicked() and self.phase in (
            self.PHASE_MENU,
            self.PHASE_ACT,
            self.PHASE_ITEM,
            self.PHASE_INTRO,
        ):
            gx, gy = inp.mouse_grid()
            if gx < 48 and gy < 12:
                self.examine.show(self.enemy.get("art_id", self.enemy_id))
                return
            if self.phase == self.PHASE_ITEM and 48 <= gx <= 72:
                slots = [s for s in self.profile.inventory.slots if s.item_id]
                if slots:
                    slot = slots[min(self.item_cursor, len(slots) - 1)]
                    self.examine.show(slot.item_id)
                return

        if self.phase in (self.PHASE_MENU, self.PHASE_ACT, self.PHASE_ITEM):
            if inp.nav_up_pressed():
                if self.phase == self.PHASE_ACT:
                    self.act_cursor = max(0, self.act_cursor - 1)
                elif self.phase == self.PHASE_ITEM:
                    self.item_cursor = max(0, self.item_cursor - 1)
                else:
                    self.menu_cursor = max(0, self.menu_cursor - 1)
            if inp.nav_down_pressed():
                if self.phase == self.PHASE_ACT:
                    self.act_cursor = min(len(self.enemy["acts"]) - 1, self.act_cursor + 1)
                elif self.phase == self.PHASE_ITEM:
                    slots = [s for s in self.profile.inventory.slots if s.item_id]
                    self.item_cursor = min(max(0, len(slots) - 1), self.item_cursor + 1)
                else:
                    self.menu_cursor = min(3, self.menu_cursor + 1)

        if inp.pressed_escape():
            if self.phase != self.PHASE_MENU:
                self.phase = self.PHASE_MENU
            return

        if not inp.action_pressed():
            return

        if self.phase == self.PHASE_MENU:
            choice = self.MENU[self.menu_cursor]
            if choice == "Fight":
                self.phase = self.PHASE_FIGHT
                self.qte.start()
            elif choice == "Act":
                self.phase = self.PHASE_ACT
            elif choice == "Item":
                self.phase = self.PHASE_ITEM
            elif choice == "Mercy":
                if mercy_available(self.scan_flags):
                    self.result = "spare"
                    spawn_companion(self.world_state, self.enemy_id, self.enemies)
                    self._log("Пощада.")
                    self.phase = self.PHASE_END
                else:
                    self._log("Mercy недоступен — нужен Scan.")
        elif self.phase == self.PHASE_ACT:
            act = self.enemy["acts"][self.act_cursor]
            self._log(act["text"][:50])
            apply_scan_effect(
                act.get("scan_effect"),
                self.scan_flags,
                self.world_state.discovered_recipes,
                self.log,
            )
            self.world_state.scan_flags.add(act["id"])
            self.phase = self.PHASE_MENU
            self._start_dodge()
        elif self.phase == self.PHASE_ITEM:
            slots = [s for s in self.profile.inventory.slots if s.item_id]
            if slots:
                slot = slots[min(self.item_cursor, len(slots) - 1)]
                data = load_items().get(slot.item_id, {})
                eff = data.get("effect", {})
                if eff.get("heal"):
                    self.profile.heal(eff["heal"])
                    self.profile.inventory.remove(slot.item_id, 1)
                    self._log(f"Использован {data.get('name', slot.item_id)}")
            self.phase = self.PHASE_MENU
            self._start_dodge()

    def _grant_drops(self):
        for drop in self.enemy.get("material_drops", []):
            from src.data.art_loader import load_materials

            mats = load_materials()
            sm = mats.get(drop["id"], {}).get("stack_max", 20)
            self.profile.inventory.add(drop["id"], drop["count"], sm)

    def draw(self, buf: ScreenBuffer):
        buf.clear()
        buf.draw_box(0, 0, SCREEN_W, SCREEN_H, bg=COLOR_UI_BG)
        draw_enemy_portrait(buf, self.enemy.get("art_id", self.enemy_id))
        buf.draw_text(50, 2, self.enemy["name"], fg=COLOR_HIGHLIGHT)
        buf.draw_text(50, 3, f"HP {self.enemy_hp}/{self.enemy['hp']}", fg=COLOR_HP)
        buf.draw_text(50, 4, f"Вы: {self.profile.hp}/{self.profile.max_hp()}", fg=COLOR_HP)

        if self.phase == self.PHASE_INTRO:
            buf.draw_text(20, 20, self.enemy["name"] + " появился!", fg=COLOR_TEXT)
            buf.draw_text(20, 22, "Enter — продолжить", fg=COLOR_TEXT)
        elif self.phase == self.PHASE_DODGE:
            bx, by = 30, 14
            bw, bh = int(self.box_w) + 2, int(self.box_h) + 2
            buf.draw_box(bx, by, bw, bh, "SOUL", fg=COLOR_UI_BORDER)
            sx = bx + 1 + int(self.soul_x)
            sy = by + 1 + int(self.soul_y)
            buf.set(sx, sy, "♥", fg=(255, 80, 120))
            if self.pattern:
                for b in self.pattern.active_bullets():
                    px = bx + 1 + int(b.x)
                    py = by + 1 + int(b.y)
                    fg = (255, 255, 100) if self.reveal_tell else (200, 200, 220)
                    if buf.in_bounds(px, py):
                        buf.set(px, py, b.char, fg=fg)
        elif self.phase == self.PHASE_FIGHT:
            buf.draw_text(30, 18, "QTE — Space в зелёной зоне", fg=COLOR_TEXT)
            bar_x, bar_y, bar_w = 25, 22, 40
            buf.draw_text(bar_x, bar_y - 1, "[" + " " * bar_w + "]", fg=COLOR_TEXT)
            pos = int(self.qte.cursor * bar_w)
            ws = int(self.qte.window_start * bar_w)
            we = int(self.qte.window_end * bar_w)
            for i in range(bar_w):
                ch = " "
                if ws <= i <= we:
                    ch = "="
                if i == pos:
                    ch = "|"
                buf.set(bar_x + 1 + i, bar_y, ch, fg=(100, 200, 100) if ws <= i <= we else COLOR_TEXT)
        else:
            menu_y = 12
            buf.draw_box(48, menu_y, 24, 10, "БОЙ")
            if self.phase == self.PHASE_MENU:
                for i, item in enumerate(self.MENU):
                    fg = COLOR_MERcy if item == "Mercy" else COLOR_HIGHLIGHT if i == self.menu_cursor else COLOR_TEXT
                    buf.draw_text(50, menu_y + 2 + i, f"> {item}" if i == self.menu_cursor else f"  {item}", fg=fg)
            elif self.phase == self.PHASE_ACT:
                for i, act in enumerate(self.enemy["acts"]):
                    fg = COLOR_HIGHLIGHT if i == self.act_cursor else COLOR_TEXT
                    buf.draw_text(50, menu_y + 2 + i, act["label"][:20], fg=fg)
            elif self.phase == self.PHASE_ITEM:
                slots = [s for s in self.profile.inventory.slots if s.item_id]
                items = load_items()
                for i, slot in enumerate(slots[:6]):
                    fg = COLOR_HIGHLIGHT if i == self.item_cursor else COLOR_TEXT
                    nm = items.get(slot.item_id, {}).get("name", slot.item_id)
                    buf.draw_text(50, menu_y + 2 + i, nm[:18], fg=fg)

        for i, line in enumerate(self.log[-6:]):
            buf.draw_text(2, SCREEN_H - 8 + i, line[:90], fg=COLOR_TEXT)

        if self.phase == self.PHASE_END:
            msg = {"kill": "Победа.", "spare": "Пощада.", "lose": "Поражение..."}.get(self.result, "")
            buf.draw_text(30, 24, msg, fg=COLOR_HIGHLIGHT)
            buf.draw_text(30, 26, "Enter — продолжить", fg=COLOR_TEXT)

        self.examine.draw(buf)
