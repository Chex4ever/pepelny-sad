"""Pygame mixer wrapper: SFX pools, ambient loops, music crossfade."""
from __future__ import annotations

import json
import os
import random
import time

import pygame

from src.constants import AUDIO_DIR


class AudioManager:
    FOOTSTEP_COOLDOWN_MS = 120
    FOOTSTEP_GAIN = 0.5

    def __init__(self):
        self.enabled = False
        self._base_path = ""
        self._manifest: dict = {}
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._groups: dict[str, list[str]] = {}
        self._loop_channels: dict[str, pygame.mixer.Channel] = {}
        self._loop_targets: dict[str, float] = {}
        self._loop_current: dict[str, float] = {}
        self._master_sfx = 0.8
        self._master_ambient = 0.5
        self._master_music = 0.55
        self._current_music: str | None = None
        self._music_paused = False
        self._last_footstep_ms = 0.0
        self._foot_side = 0
        self._drip_timer_ms = 0.0
        self._drip_next_ms = 12000.0
        self._voice_last_ms = 0.0
        self._voice_cooldown_ms = 18.0

    def init(self, base_path: str | None = None) -> bool:
        self._base_path = base_path or ""
        audio_dir = AUDIO_DIR or os.path.join(self._base_path, "assets", "audio")
        manifest_path = os.path.join(audio_dir, "manifest.json")
        if os.environ.get("SDL_AUDIODRIVER") == "dummy":
            return False
        if not os.path.isfile(manifest_path):
            return False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)
            self._manifest = data.get("sounds", {})
            self._load_sounds(audio_dir)
            self.enabled = True
            return True
        except (pygame.error, OSError, json.JSONDecodeError):
            self.enabled = False
            return False

    def _load_sounds(self, audio_dir: str):
        for sid, entry in self._manifest.items():
            if "group" in entry and isinstance(entry["group"], list):
                self._groups[sid] = list(entry["group"])
                continue
            rel = entry.get("file")
            if not rel:
                continue
            path = os.path.join(audio_dir, rel)
            if os.path.isfile(path):
                self._sounds[sid] = pygame.mixer.Sound(path)

    def _pick_sound_id(self, sound_id: str) -> str | None:
        if sound_id in self._groups:
            pool = self._groups[sound_id]
            return random.choice(pool) if pool else None
        if sound_id in self._sounds:
            return sound_id
        return None

    def play_sfx(self, sound_id: str, *, volume: float = 1.0) -> bool:
        if not self.enabled:
            return False
        sid = self._pick_sound_id(sound_id)
        if not sid or sid not in self._sounds:
            return False
        entry = self._manifest.get(sid, {})
        base_vol = float(entry.get("volume", 1.0))
        vol = max(0.0, min(1.0, volume * base_vol * self._master_sfx))
        ch = self._sounds[sid].play()
        if ch:
            ch.set_volume(vol)
        return True

    def play_footstep(self, surface: str) -> bool:
        now = time.monotonic() * 1000
        if now - self._last_footstep_ms < self.FOOTSTEP_COOLDOWN_MS:
            return False
        self._last_footstep_ms = now
        group_id = f"footstep_{surface}"
        vol_jitter = random.uniform(0.65, 0.95)
        self._foot_side = 1 - self._foot_side
        side_mod = 1.03 if self._foot_side else 0.97
        return self.play_sfx(group_id, volume=vol_jitter * side_mod * self.FOOTSTEP_GAIN)

    def play_voice_blip(self, voice: str, variant: int = 0, *, volume: float = 1.0) -> bool:
        if not self.enabled:
            return False
        now = time.monotonic() * 1000
        if now - self._voice_last_ms < self._voice_cooldown_ms:
            return False
        self._voice_last_ms = now
        group_id = f"voice_{voice}"
        pool = self._groups.get(group_id)
        sid = None
        if pool:
            sid = pool[variant % len(pool)]
        if sid is None:
            alt = f"voice_{voice}_{variant}"
            if alt in self._sounds:
                sid = alt
        if sid is None:
            sid = self._pick_sound_id("voice_default")
        if sid is None or sid not in self._sounds:
            return False
        entry = self._manifest.get(sid, {})
        base_vol = float(entry.get("volume", 0.35))
        vol = max(0.0, min(1.0, volume * base_vol * self._master_sfx * random.uniform(0.92, 1.05)))
        ch = self._sounds[sid].play()
        if ch:
            ch.set_volume(vol)
        return True

    def set_loop(self, sound_id: str, active: bool, volume: float = 0.0):
        if not self.enabled:
            return
        target = max(0.0, min(1.0, volume * self._master_ambient))
        self._loop_targets[sound_id] = target if active else 0.0
        if sound_id not in self._loop_current:
            self._loop_current[sound_id] = 0.0
        ch = self._loop_channels.get(sound_id)
        if active and target > 0.01 and sound_id in self._sounds:
            if ch is None or not ch.get_busy():
                ch = self._sounds[sound_id].play(loops=-1)
                if ch:
                    self._loop_channels[sound_id] = ch
                    ch.set_volume(self._loop_current[sound_id])

    def play_music(self, track_id: str | None, fade_ms: int = 2000):
        if not self.enabled:
            return
        if track_id == self._current_music and track_id is not None:
            return
        if track_id is None:
            pygame.mixer.music.fadeout(fade_ms)
            self._current_music = None
            return
        entry = self._manifest.get(track_id, {})
        rel = entry.get("file")
        if not rel:
            return
        audio_dir = AUDIO_DIR or os.path.join(self._base_path, "assets", "audio")
        path = os.path.join(audio_dir, rel)
        if not os.path.isfile(path):
            return
        vol = float(entry.get("volume", 0.45)) * self._master_music
        if self._current_music:
            pygame.mixer.music.fadeout(min(fade_ms, 800))
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        pygame.mixer.music.play(-1, fade_ms=fade_ms)
        self._current_music = track_id
        self._music_paused = False

    def pause_music(self):
        if self.enabled and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self._music_paused = True

    def resume_music(self):
        if self.enabled and self._music_paused:
            pygame.mixer.music.unpause()
            self._music_paused = False

    def update(self, dt_ms: int):
        if not self.enabled:
            return
        lerp = min(1.0, dt_ms / 400.0)
        for sid, target in self._loop_targets.items():
            cur = self._loop_current.get(sid, 0.0)
            cur += (target - cur) * lerp
            self._loop_current[sid] = cur
            ch = self._loop_channels.get(sid)
            if ch:
                if target <= 0.01 and cur < 0.01:
                    ch.stop()
                else:
                    entry = self._manifest.get(sid, {})
                    base = float(entry.get("volume", 0.4))
                    ch.set_volume(max(0.0, min(1.0, cur * base * self._master_ambient)))
        self._drip_timer_ms += dt_ms
        if self._drip_timer_ms >= self._drip_next_ms:
            self._drip_timer_ms = 0.0
            self._drip_next_ms = random.uniform(8000, 20000)
            if self._loop_targets.get("cave", 0) > 0.05:
                self.play_sfx("drip", volume=random.uniform(0.5, 0.9))
