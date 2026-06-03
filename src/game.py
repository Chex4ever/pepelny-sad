"""Game loop and scene management."""
from __future__ import annotations

import os
import random
import sys

import pygame

from src.battle.battle_scene import BattleScene
from src.constants import CELL_H, CELL_W, FPS, SCREEN_H, SCREEN_W, init_paths
from src.data.art_init import ensure_art_files
from src.input import InputState
from src.overworld.overworld_scene import OverworldScene
from src.progression.player_profile import PlayerProfile
from src.render.renderer import AsciiRenderer
from src.render.screen_buffer import ScreenBuffer
from src.story.narrative import ENDINGS, pick_ending
from src.ui.title_screen import TitleScreen
from src.world.world_map import WorldMap
from src.world.world_state import WorldState


class Game:
    def __init__(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        init_paths(base)
        ensure_art_files()
        pygame.init()
        pygame.display.set_caption("Пепельный Сад")
        self.screen = pygame.display.set_mode((SCREEN_W * CELL_W, SCREEN_H * CELL_H))
        pygame.event.clear()
        pygame.event.pump()
        self.renderer = AsciiRenderer(self.screen)
        self.buffer = ScreenBuffer(SCREEN_W, SCREEN_H)
        self.input = InputState()
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = "title"
        self.world_state = WorldState(world_seed=random.randint(1, 99999))
        self.profile = PlayerProfile()
        self.world_map = WorldMap(self.world_state.world_seed)
        self.overworld: OverworldScene | None = None
        self.battle: BattleScene | None = None
        self.ending_data = None
        self.enemy_id_boss = False
        self.title_seed = self.world_state.world_seed
        self.title_screen = TitleScreen()
        self.title_frame = 0
        self._try_load_music(base)

    def _try_load_music(self, base):
        try:
            pygame.mixer.init()
            surf = os.path.join(base, "assets", "surface.ogg")
            if os.path.isfile(surf):
                pygame.mixer.music.load(surf)
                pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def serialize_state(self) -> dict:
        inv = [(s.item_id, s.count) for s in self.profile.inventory.slots]
        return {
            "world_seed": self.world_state.world_seed,
            "layer": self.world_state.layer,
            "spare_count": self.world_state.spare_count,
            "kill_count": self.world_state.kill_count,
            "companions": list(self.world_state.companions),
            "discovered_recipes": list(self.world_state.discovered_recipes),
            "scan_flags": list(self.world_state.scan_flags),
            "story_flags": list(self.world_state.story_flags),
            "turn_count": self.world_state.turn_count,
            "dungeon_entered": self.world_state.dungeon_entered,
            "boss_cleared": self.world_state.boss_cleared,
            "defeated_battles": list(self.world_state.defeated_battles),
            "hp": self.profile.hp,
            "inventory": inv,
            "equipment": dict(self.profile.equipment.slots),
            "modules": list(self.profile.installed_modules),
            "player_pos": (self.overworld.player.x, self.overworld.player.y) if self.overworld else (20, 24),
        }

    def restore_state(self, data: dict):
        self.world_state.world_seed = data.get("world_seed", 42)
        self.world_state.layer = data.get("layer", "surface")
        self.world_state.spare_count = data.get("spare_count", 0)
        self.world_state.kill_count = data.get("kill_count", 0)
        self.world_state.companions = list(data.get("companions", []))
        self.world_state.discovered_recipes = set(data.get("discovered_recipes", []))
        self.world_state.scan_flags = set(data.get("scan_flags", []))
        self.world_state.story_flags = set(data.get("story_flags", []))
        self.world_state.turn_count = data.get("turn_count", 0)
        self.world_state.dungeon_entered = data.get("dungeon_entered", False)
        self.world_state.boss_cleared = data.get("boss_cleared", False)
        self.world_state.defeated_battles = set(tuple(x) for x in data.get("defeated_battles", []))
        self.world_map = WorldMap(self.world_state.world_seed)
        self.profile = PlayerProfile()
        self.profile.hp = data.get("hp", 20)
        for i, (iid, cnt) in enumerate(data.get("inventory", [])):
            if iid and i < len(self.profile.inventory.slots):
                self.profile.inventory.slots[i].item_id = iid
                self.profile.inventory.slots[i].count = cnt
        for slot, iid in data.get("equipment", {}).items():
            self.profile.equipment.equip(slot, iid)
        self.profile.installed_modules = list(data.get("modules", []))
        self.profile.refresh_capacity()
        self.overworld = OverworldScene(self)
        px, py = data.get("player_pos", (20, 24))
        self.overworld.player.x, self.overworld.player.y = px, py

    def new_game(self, seed: int | None = None):
        self.world_state = WorldState(world_seed=seed or random.randint(1, 99999))
        self.profile = PlayerProfile()
        self.profile.inventory.add("grey_herb", 3, 20)
        self.profile.inventory.add("root_fiber", 2, 20)
        self.world_map = WorldMap(self.world_state.world_seed)
        self.overworld = OverworldScene(self)
        self.scene = "overworld"

    def _on_battle_done(self, result: str):
        if self.enemy_id_boss and result in ("kill", "spare"):
            self.world_state.boss_cleared = True
            self.ending_data = ENDINGS[pick_ending(self.world_state, result)]
            self.scene = "ending"
        else:
            self.scene = "overworld"
        self.battle = None

    def run(self):
        while self.running:
            pygame.event.pump()
            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
            self.input.sync_keyboard()

            if self.input.pressed(pygame.K_ESCAPE) and self.scene == "title":
                self.running = False

            if self.scene == "title":
                self.title_frame += 1
                self._update_title()
                self._draw_title()
            elif self.scene == "overworld" and self.overworld:
                self.overworld.update()
                self.overworld.handle_input(self.input)
                nb = self.overworld.needs_battle
                if nb:
                    self.enemy_id_boss = nb == "warden" and self.world_state.layer == "dungeon"
                    self.battle = BattleScene(nb, self.profile, self.world_state, self._on_battle_done)
                    self.scene = "battle"
                else:
                    self.overworld.draw(self.buffer)
            elif self.scene == "battle" and self.battle:
                self.battle.update()
                self.battle.handle_input(self.input)
                self.battle.draw(self.buffer)
            elif self.scene == "ending":
                self._draw_ending()
                if self.input.confirm_pressed():
                    self.scene = "title"

            self.renderer.draw(self.buffer)
            self.clock.tick(FPS)
        pygame.quit()

    def _update_title(self):
        if self.input.confirm_pressed():
            self.new_game(self.title_seed)
        if self.input.pressed(pygame.K_r):
            self.title_seed = random.randint(1, 99999)
        if self.input.pressed(pygame.K_l):
            from src.world.save import load_game

            data = load_game()
            if data:
                self.restore_state(data)
                self.scene = "overworld"

    def _draw_title(self):
        self.title_screen.draw(
            self.buffer,
            seed=self.title_seed,
            frame=self.title_frame,
            title_seed=self.title_seed,
        )

    def _draw_ending(self):
        from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT

        self.buffer.clear()
        if self.ending_data:
            self.buffer.draw_text(30, 8, self.ending_data["title"], fg=COLOR_HIGHLIGHT)
            for i, line in enumerate(self.ending_data["lines"]):
                self.buffer.draw_text(20, 14 + i, line, fg=COLOR_TEXT)
        self.buffer.draw_text(28, 28, "Enter — в меню", fg=COLOR_TEXT)


def main():
    Game().run()


if __name__ == "__main__":
    main()
