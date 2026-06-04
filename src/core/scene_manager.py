"""Scene switching and per-frame updates."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.battle.battle_scene import BattleScene
from src.core.scene_context import SceneContext
from src.core.save_service import SaveService
from src.i18n import t
from src.story.narrative import get_ending, pick_ending
from src.world.dungeon_stitcher import ensure_dungeon
from src.world.save import load_game, save_game

if TYPE_CHECKING:
    from src.game import Game


class SceneManager:
    def __init__(self, game: Game):
        self.game = game

    def ctx(self) -> SceneContext:
        g = self.game
        return SceneContext(
            world_state=g.world_state,
            profile=g.profile,
            world_map=g.world_map,
            audio=g.audio,
            ambient=g.ambient,
            music=g.music,
            windows=g.windows,
            game=g,
            ending_data=g.ending_data,
            title_seed=g.title_seed,
            title_start_ms=g.title_start_ms,
        )

    def apply_pending_action(self) -> None:
        action = self.game._pending_action
        self.game._pending_action = None
        if not action or not self.game.overworld:
            return
        if action == "dungeon_enter":
            self.game.world_state.layer = "dungeon"
            ensure_dungeon(self.game.world_state, self.game.world_map)
            self.game.overworld.player.x, self.game.overworld.player.y = 2, 2
            self.game.overworld.log.add("Спуск в подземелье.")
        elif action == "surface_exit":
            self.game.world_state.layer = "surface"
            self.game.overworld.player.x, self.game.overworld.player.y = 80, 24
            self.game.overworld.log.add("Выход на поверхность.")
        if self.game.overworld:
            self.game.music.on_layer(self.game.world_state.layer)

    def start_transition(self, target_scene: str) -> None:
        def midpoint():
            self.game.scene = target_scene
            if target_scene == "intro":
                self.game.intro.reset()
            if target_scene == "overworld":
                log = self.game.windows.get("log")
                if log:
                    log.show()
                    if not log.lines:
                        log.add(t("ui.log.welcome"))
            if target_scene == "title":
                log = self.game.windows.get("log")
                if log:
                    log.close()
            self.apply_pending_action()
            self.game.music.on_scene(self.game.scene)
            if self.game.overworld:
                self.game.music.on_layer(self.game.world_state.layer)
                self.game.music.on_weather(self.game.overworld.weather.active)

        self.game.transition.start("out", pending_scene=target_scene, callback=midpoint)

    def on_battle_done(self, result: str) -> None:
        if self.game.enemy_id_boss and result in ("kill", "spare"):
            self.game.world_state.boss_cleared = True
            self.game.ending_data = get_ending(pick_ending(self.game.world_state, result))
            self.start_transition("ending")
        else:
            self.start_transition("overworld")
        self.game.battle = None

    def handle_pause_action(self, action: str | None) -> None:
        if action == "main_menu":
            self.start_transition("title")
            self.game.title_start_ms = pygame.time.get_ticks()
        elif action == "save":
            save_game(SaveService.serialize(self.game))
            if self.game.overworld:
                self.game.overworld.log.add(t("ui.log.saved"))
        elif action == "save_quit":
            save_game(SaveService.serialize(self.game))
            self.game.running = False
        elif action == "quit":
            self.game.running = False

    def run_frame(self, dt_ms: int) -> None:
        g = self.game
        inp = g.input

        if g.transition.blocks_input():
            g.transition.update(dt_ms)
            if g.scene == "title":
                g._draw_title()
            elif g.scene == "intro":
                g.intro.draw(g.buffer)
            g._render_frame()
            return

        g.transition.update(dt_ms)
        g.audio.update(dt_ms)

        pause = g.pause
        help_w = g.help
        debug_w = g.debug

        if inp.pressed_f1() and g.scene != "title":
            help_w.toggle()
            if help_w.visible and getattr(g, "tutorial", None):
                g.tutorial.notify_help_or_pause()
        if inp.pressed_f4() and g.scene != "title":
            debug_w.toggle()
        opened_pause_this_frame = False
        if inp.pressed_escape():
            if help_w.visible:
                help_w.close()
            elif debug_w.visible:
                debug_w.close()
            elif pause.visible:
                if pause.confirm_quit:
                    pause.confirm_quit = False
                else:
                    pause.close()
                    g.audio.resume_music()
            elif g.windows.examine_open():
                g.windows.close_examine()
            elif g.scene == "title":
                g.running = False
            elif g.scene in ("overworld", "battle"):
                pause.toggle()
                opened_pause_this_frame = True
                g.audio.pause_music()
                if getattr(g, "tutorial", None):
                    g.tutorial.notify_help_or_pause()

        pause_action = None
        if pause.visible and not (opened_pause_this_frame and inp.pressed_escape()):
            pause_action = pause.handle_menu_input(inp)
        if pause_action:
            self.handle_pause_action(pause_action)

        help_w.handle_keys(inp)
        debug_w.handle_keys(inp)

        ui_blocked = pause.visible

        if g.scene == "title":
            log = g.windows.get("log")
            if log:
                log.close()
            g._update_title()
            g._draw_title()
        elif g.scene == "intro":
            g.intro.update(dt_ms, g.audio)
            if g.intro.handle_input(inp):
                self.start_transition("overworld")
            g.intro.draw(g.buffer)
        elif g.scene == "overworld" and g.overworld:
            g.perf.begin_frame()
            g.overworld.update(dt_ms)
            if getattr(g, "tutorial", None):
                g.tutorial.update_frame()
                if getattr(g, "tutorial_window", None):
                    g.tutorial_window.set_text(g.tutorial.current_text())
            g.music.on_weather(g.overworld.weather.active)
            g.music.on_turn(g.world_state.turn_count)
            if not ui_blocked:
                g.overworld.handle_input(inp)
                self.apply_pending_action()
            nb = g.overworld.needs_battle
            if nb:
                g.enemy_id_boss = nb == "warden" and g.world_state.layer == "dungeon"
                g.battle = BattleScene(
                    nb,
                    g.profile,
                    g.world_state,
                    self.on_battle_done,
                    g.audio,
                    examine=g.windows.get("examine"),
                )
                self.start_transition("battle")
            else:
                if debug_w.visible:
                    debug_w.set_lines(g.overworld.debug_lines(g.fps))
                g.overworld.draw(g.buffer, inp)
            g.perf.end_frame()
        elif g.scene == "battle" and g.battle:
            g.battle.update()
            if not ui_blocked:
                g.battle.handle_input(inp)
            g.battle.draw(g.buffer)
        elif g.scene == "ending":
            g._draw_ending()
            if inp.confirm_pressed():
                self.start_transition("title")
                g.title_start_ms = pygame.time.get_ticks()

        g._render_frame()
