"""Game loop and scene management."""
from __future__ import annotations

import os
import random

import pygame

from src.audio.ambient_controller import AmbientController
from src.audio.audio_manager import AudioManager
from src.audio.music_controller import MusicController
from src.constants import CELL_H, CELL_W, FPS, SCREEN_H, SCREEN_W, init_paths
from src.i18n import init_locale_from_env, t
from src.core.loading_flow import LoadingFlow
from src.core.perf_stats import PerfStats
from src.core.save_service import SaveService
from src.core.scene_manager import SceneManager
from src.data.art_init import ensure_art_files
from src.input import InputState
from src.progression.player_profile import PlayerProfile
from src.render.render_mode import init_render_mode_from_env, render_mode
from src.render.renderer import AsciiRenderer
from src.render.screen_buffer import ScreenBuffer
from src.render.transitions import TransitionManager
from src.scenes.overworld.overworld_scene import OverworldScene
from src.story.intro import IntroScene
from src.ui.title_screen import TitleScreen
from src.ui.windows.character_sheet_window import CharacterSheetWindow
from src.ui.windows.craft_window import CraftWindow
from src.ui.windows.debug_window import DebugWindow
from src.ui.windows.examine_window import ExamineWindow
from src.ui.windows.help_window import HelpWindow
from src.ui.windows.log_window import LogWindow
from src.ui.windows.pause_window import PauseWindow
from src.ui.tutorial.tutorial_controller import TutorialController
from src.ui.windows.tutorial_window import TutorialWindow
from src.ui.windows.window_manager import WindowManager
from src.world.save import load_game
from src.world.world_map import WorldMap
from src.world.world_state import WorldState
from src.version import get_version


class Game:
    def __init__(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        init_paths(base)
        init_locale_from_env()
        ensure_art_files()
        pygame.init()
        init_render_mode_from_env()
        pygame.display.set_caption(f"Пепельный Сад v{get_version()}")
        pixel_w, pixel_h = SCREEN_W * CELL_W, SCREEN_H * CELL_H
        mode_flags = 0
        if render_mode() == "gpu":
            from src.render.gpu.context import configure_bench_gl_attributes

            configure_bench_gl_attributes()
            mode_flags = pygame.OPENGL | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((pixel_w, pixel_h), mode_flags)
        if hasattr(pygame.key, "stop_text_input"):
            pygame.key.stop_text_input()
        pygame.event.clear()
        pygame.event.pump()
        self.renderer = AsciiRenderer(self.screen)
        self.gpu_presenter = None
        if render_mode() == "gpu":
            from src.render.gpu.presenter import GpuPresenter

            self.gpu_presenter = GpuPresenter(self.screen, self.renderer)
        self.buffer = ScreenBuffer(SCREEN_W, SCREEN_H)
        self.input = InputState()
        self.clock = pygame.time.Clock()
        self.fps = 0.0
        self.perf = PerfStats()
        self.running = True
        self.scene = "title"
        self.world_state = WorldState(world_seed=random.randint(1, 99999))
        self.profile = PlayerProfile()
        self.world_map = WorldMap(self.world_state.world_seed)
        self.world_map.perf_stats = self.perf
        self.overworld: OverworldScene | None = None
        self.battle = None
        self.ending_data = None
        self.enemy_id_boss = False
        self.title_seed = self.world_state.world_seed
        self.title_screen = TitleScreen()
        self.title_start_ms = pygame.time.get_ticks()
        self.intro = IntroScene()
        self.windows = WindowManager()
        for w in (
            LogWindow(),
            ExamineWindow(),
            CharacterSheetWindow(),
            CraftWindow(),
            HelpWindow(),
            DebugWindow(),
            PauseWindow(),
            TutorialWindow(),
        ):
            self.windows.register(w)
        self.pause = self.windows.get("pause")
        self.help = self.windows.get("help")
        self.debug = self.windows.get("debug")
        self.tutorial = TutorialController(self)
        self.tutorial_window = self.windows.get("tutorial")
        self.transition = TransitionManager()
        self.loading = LoadingFlow()
        self._pending_action: str | None = None
        self._fade_overlay = pygame.Surface(
            (SCREEN_W * CELL_W, SCREEN_H * CELL_H), pygame.SRCALPHA
        )
        self.audio = AudioManager()
        self.audio.init(base)
        self.ambient = AmbientController(self.audio)
        self.music = MusicController(self.audio)
        self.music.on_scene(self.scene)
        self.scenes = SceneManager(self)

    def request_scene(self, action: str):
        self._pending_action = action

    def serialize_state(self) -> dict:
        return SaveService.serialize(self)

    def restore_state(self, data: dict):
        SaveService.restore(self, data)

    def _start_transition(self, target_scene: str) -> None:
        self.scenes.start_transition(target_scene)

    def _on_battle_done(self, result: str) -> None:
        self.scenes.on_battle_done(result)

    def request_new_game(self, seed: int | None = None) -> None:
        """Fade out title, show loading, then intro with fade-in."""
        self.loading.start_new_game(self, seed if seed is not None else self.title_seed)

    def new_game(self, seed: int | None = None):
        from src.core.new_game_loader import build_new_game

        build_new_game(self, seed)
        self.intro.reset()
        self.scene = "intro"

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            self.fps = self.clock.get_fps()
            pygame.event.pump()
            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)
            self.input.sync_keyboard()
            self.scenes.run_frame(dt_ms)
        pygame.quit()

    def examine_open(self) -> bool:
        return self.windows.examine_open()

    def _close_examine(self):
        self.windows.close_examine()

    def _gpu_active(self) -> bool:
        return (
            render_mode() == "gpu"
            and self.gpu_presenter is not None
            and self.gpu_presenter.available
        )

    def _render_frame(self):
        perf = self.perf
        with perf.measure("overlay_ui"):
            self.pause.draw(self.buffer)
            self.help.draw(self.buffer)
            self.debug.draw(self.buffer)
        fade_alpha = self.transition.alpha()
        gpu = self._gpu_active()
        use_gpu_map = gpu and self.scene == "overworld" and self.overworld is not None
        with perf.measure("present"):
            if use_gpu_map:
                self.gpu_presenter.render_overworld(self, fade_alpha=fade_alpha)
            elif gpu:
                self.gpu_presenter.present_buffer(self.buffer, fade_alpha=fade_alpha)
            else:
                self.renderer.draw(self.buffer)
                if fade_alpha > 0:
                    self._fade_overlay.fill((0, 0, 0, fade_alpha))
                    self.screen.blit(self._fade_overlay, (0, 0))
                    pygame.display.flip()

    def _update_title(self):
        if self.input.confirm_pressed() and not self.loading.active:
            self.audio.play_sfx("ui_confirm")
            self.request_new_game(self.title_seed)
        if self.input.pressed(pygame.K_r):
            self.title_seed = random.randint(1, 99999)
        if self.input.pressed(pygame.K_l):
            data = load_game()
            if data:
                self.restore_state(data)
                self.scene = "overworld"
                log = self.windows.get("log")
                if log:
                    log.show()
                self.music.on_scene("overworld")
                self.music.on_layer(self.world_state.layer)

    def _draw_title(self):
        elapsed = pygame.time.get_ticks() - self.title_start_ms
        self.title_screen.draw(
            self.buffer, seed=self.title_seed, elapsed_ms=elapsed, title_seed=self.title_seed
        )

    def _draw_ending(self):
        from src.constants import COLOR_HIGHLIGHT, COLOR_TEXT

        self.buffer.clear()
        if self.ending_data:
            self.buffer.draw_text(30, 8, self.ending_data["title"], fg=COLOR_HIGHLIGHT)
            for i, line in enumerate(self.ending_data["lines"]):
                self.buffer.draw_text(20, 14 + i, line, fg=COLOR_TEXT)
        self.buffer.draw_text(28, 28, t("ending.menu_hint"), fg=COLOR_TEXT)


def main():
    Game().run()


if __name__ == "__main__":
    main()
