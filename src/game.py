"""Game loop and scene management."""
from __future__ import annotations

import os
import random

import pygame

from src.audio.ambient_controller import AmbientController
from src.audio.audio_manager import AudioManager
from src.audio.music_controller import MusicController
from src.battle.battle_scene import BattleScene
from src.constants import CELL_H, CELL_W, FPS, SCREEN_H, SCREEN_W, init_paths
from src.data.art_init import ensure_art_files
from src.input import InputState
from src.overworld.overworld_scene import OverworldScene
from src.progression.player_profile import PlayerProfile
from src.render.renderer import AsciiRenderer
from src.render.screen_buffer import ScreenBuffer
from src.render.transitions import TransitionManager
from src.story.intro import IntroScene
from src.story.narrative import ENDINGS, pick_ending
from src.ui.help_panel import HelpPanel
from src.ui.pause_menu import PauseMenu
from src.ui.title_screen import TitleScreen
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.world_map import WorldMap
from src.world.world_state import WorldState
from src.world.save import load_game, save_game


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
        self.title_start_ms = pygame.time.get_ticks()
        self.intro = IntroScene()
        self.pause = PauseMenu()
        self.help = HelpPanel()
        self.transition = TransitionManager()
        self._pending_action: str | None = None
        self._fade_overlay = pygame.Surface(
            (SCREEN_W * CELL_W, SCREEN_H * CELL_H), pygame.SRCALPHA
        )
        self.audio = AudioManager()
        self.audio.init(base)
        self.ambient = AmbientController(self.audio)
        self.music = MusicController(self.audio)
        self.music.on_scene(self.scene)

    def request_scene(self, action: str):
        self._pending_action = action

    def _apply_pending_action(self):
        action = self._pending_action
        self._pending_action = None
        if not action or not self.overworld:
            return
        if action == "dungeon_enter":
            self.world_state.layer = "dungeon"
            ensure_dungeon(self.world_state, self.world_map)
            self.overworld.player.x, self.overworld.player.y = 2, 2
            self.overworld.log.add("Спуск в подземелье.")
        elif action == "surface_exit":
            self.world_state.layer = "surface"
            self.overworld.player.x, self.overworld.player.y = 80, 24
            self.overworld.log.add("Выход на поверхность.")
        if self.overworld:
            self.music.on_layer(self.world_state.layer)

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
            "dungeon_explored": list(self.world_map.dungeon_explored),
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
        self.world_map.dungeon_explored = set(tuple(x) for x in data.get("dungeon_explored", []))
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
        self.intro.reset()
        self._start_transition("intro")

    def _start_transition(self, target_scene: str):
        def midpoint():
            self.scene = target_scene
            if target_scene == "intro":
                self.intro.reset()
            self._apply_pending_action()
            self.music.on_scene(self.scene)
            if self.overworld:
                self.music.on_layer(self.world_state.layer)
                self.music.on_weather(self.overworld.weather.active)

        self.transition.start("out", pending_scene=target_scene, callback=midpoint)

    def _on_battle_done(self, result: str):
        if self.enemy_id_boss and result in ("kill", "spare"):
            self.world_state.boss_cleared = True
            self.ending_data = ENDINGS[pick_ending(self.world_state, result)]
            self._start_transition("ending")
        else:
            self._start_transition("overworld")
        self.battle = None

    def _handle_pause_action(self, action: str | None):
        if action == "main_menu":
            self._start_transition("title")
            self.title_start_ms = pygame.time.get_ticks()
        elif action == "save":
            save_game(self.serialize_state())
            if self.overworld:
                self.overworld.log.add("Сохранено.")
        elif action == "save_quit":
            save_game(self.serialize_state())
            self.running = False
        elif action == "quit":
            self.running = False

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            pygame.event.pump()
            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
            self.input.sync_keyboard()

            if self.transition.blocks_input():
                self.transition.update(dt_ms)
                if self.scene == "title":
                    self._draw_title()
                elif self.scene == "intro":
                    self.intro.draw(self.buffer)
                self._render_frame()
                continue

            self.transition.update(dt_ms)
            self.audio.update(dt_ms)

            if self.input.pressed_f1() and self.scene != "title":
                self.help.toggle()
            if self.input.pressed_escape():
                if self.help.open:
                    self.help.close()
                elif self.pause.open:
                    self.pause.close()
                    self.audio.resume_music()
                elif self.examine_open():
                    self._close_examine()
                elif self.scene == "title":
                    self.running = False
                elif self.scene in ("overworld", "battle"):
                    self.pause.toggle()
                    if self.pause.open:
                        self.audio.pause_music()
                    else:
                        self.audio.resume_music()

            pause_action = self.pause.handle_input(self.input)
            if pause_action:
                self._handle_pause_action(pause_action)

            if self.scene == "title":
                self._update_title()
                self._draw_title()
            elif self.scene == "intro":
                self.intro.update(dt_ms, self.audio)
                if self.intro.handle_input(self.input):
                    self._start_transition("overworld")
                self.intro.draw(self.buffer)
            elif self.scene == "overworld" and self.overworld:
                self.overworld.update(dt_ms)
                self.music.on_weather(self.overworld.weather.active)
                self.music.on_turn(self.world_state.turn_count)
                if not self.pause.open and not self.help.open:
                    self.overworld.handle_input(self.input)
                    self._apply_pending_action()
                nb = self.overworld.needs_battle
                if nb:
                    self.enemy_id_boss = nb == "warden" and self.world_state.layer == "dungeon"
                    self.battle = BattleScene(
                        nb, self.profile, self.world_state, self._on_battle_done, self.audio
                    )
                    self._start_transition("battle")
                else:
                    self.overworld.draw(self.buffer, self.input)
            elif self.scene == "battle" and self.battle:
                self.battle.update()
                if not self.pause.open and not self.help.open:
                    self.battle.handle_input(self.input)
                self.battle.draw(self.buffer)
            elif self.scene == "ending":
                self._draw_ending()
                if self.input.confirm_pressed():
                    self._start_transition("title")
                    self.title_start_ms = pygame.time.get_ticks()

            self._render_frame()

        pygame.quit()

    def examine_open(self) -> bool:
        if self.overworld and self.overworld.examine.open:
            return True
        if self.battle and self.battle.examine.open:
            return True
        return False

    def _close_examine(self):
        if self.overworld:
            self.overworld.examine.close()
        if self.battle:
            self.battle.examine.close()

    def _render_frame(self):
        self.pause.draw(self.buffer)
        self.help.draw(self.buffer)
        self.renderer.draw(self.buffer)
        alpha = self.transition.alpha()
        if alpha > 0:
            self._fade_overlay.fill((0, 0, 0, alpha))
            self.screen.blit(self._fade_overlay, (0, 0))
            pygame.display.flip()

    def _update_title(self):
        if self.input.confirm_pressed():
            self.audio.play_sfx("ui_confirm")
            self.new_game(self.title_seed)
        if self.input.pressed(pygame.K_r):
            self.title_seed = random.randint(1, 99999)
        if self.input.pressed(pygame.K_l):
            data = load_game()
            if data:
                self.restore_state(data)
                self.scene = "overworld"
                self.music.on_scene("overworld")
                self.music.on_layer(self.world_state.layer)

    def _draw_title(self):
        elapsed = pygame.time.get_ticks() - self.title_start_ms
        self.title_screen.draw(self.buffer, seed=self.title_seed, elapsed_ms=elapsed, title_seed=self.title_seed)

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
