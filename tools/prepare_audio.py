#!/usr/bin/env python3
"""Download CC0 audio packs and build assets/audio/ tree + manifest.json."""
from __future__ import annotations

import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import wave
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "audio"
STAGING = ROOT / "tools" / "_audio_staging"

DOWNLOADS = {
    "kenney_interface": "https://opengameart.org/sites/default/files/kenney_interfaceSounds.zip",
    "kenney_impact": "https://github.com/KenneyNL/Impact-Sounds/archive/refs/heads/main.zip",
    "kenney_rpg": "https://github.com/KenneyNL/RPG-Audio/archive/refs/heads/main.zip",
}

# FreePD public domain music — procedural fallback if download fails
MUSIC_URLS: dict[str, str] = {}


def download(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"  download {url}")
        urllib.request.urlretrieve(url, dest)
        return dest.stat().st_size > 1000
    except Exception as exc:
        print(f"  skip ({exc})")
        return False


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def to_ogg(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".ogg":
        shutil.copy2(src, dst)
        return dst
    if has_ffmpeg():
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c:a", "libvorbis", "-q:a", "4", str(dst)],
            check=True,
        )
        return dst
    # Fallback: keep WAV (pygame loads both)
    wav_dst = dst.with_suffix(".wav")
    if src.suffix.lower() != ".wav":
        shutil.copy2(src, wav_dst)
    else:
        shutil.copy2(src, wav_dst)
    return wav_dst


def write_wav(path: Path, samples: list[float], rate: int = 44100):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        frames = bytearray()
        for s in samples:
            v = max(-1.0, min(1.0, s))
            frames.extend(struct.pack("<h", int(v * 32767 * 0.85)))
        wf.writeframes(frames)


def synth_footstep(seed: int, base_hz: float, decay: float = 0.012) -> list[float]:
    rng = random.Random(seed)
    rate = 44100
    length = int(rate * 0.18)
    out = []
    for i in range(length):
        t = i / rate
        env = math.exp(-t / decay)
        noise = (rng.random() * 2 - 1) * 0.55
        tone = math.sin(2 * math.pi * base_hz * t) * 0.25
        thump = math.sin(2 * math.pi * (base_hz * 0.45) * t) * math.exp(-t / 0.025) * 0.5
        out.append((noise + tone + thump) * env)
    return out


def synth_loop(seed: int, seconds: float, fn) -> list[float]:
    rate = 44100
    n = int(rate * seconds)
    return [fn(i / rate, seed) for i in range(n)]


def synth_wind(t: float, seed: int) -> float:
    rng = random.Random(seed + int(t * 10))
    base = math.sin(t * 0.7 + seed) * 0.15
    hiss = (rng.random() * 2 - 1) * 0.08
    gust = max(0, math.sin(t * 0.35 + seed * 0.3)) * 0.12
    return base + hiss + gust


def synth_torch(t: float, seed: int) -> float:
    rng = random.Random(seed + int(t * 50))
    crack = 0.0
    if rng.random() < 0.02:
        crack = rng.random() * 0.35
    return 0.04 + crack + (rng.random() * 2 - 1) * 0.02


def synth_cave(t: float, seed: int) -> float:
    return math.sin(t * 0.5 + seed) * 0.06 + math.sin(t * 1.3) * 0.03


def synth_ember(t: float, seed: int) -> float:
    rng = random.Random(seed + int(t * 30))
    return 0.02 + (rng.random() * 0.04 if rng.random() < 0.15 else 0)


def synth_drip(seed: int) -> list[float]:
    rate = 44100
    length = int(rate * 0.35)
    out = []
    for i in range(length):
        t = i / rate
        env = math.exp(-t / 0.08)
        tone = math.sin(2 * math.pi * 880 * t) * env * 0.4
        out.append(tone + (random.Random(seed).random() * 2 - 1) * 0.05 * env)
    return out


def pitch_shift_samples(samples: list[float], factor: float) -> list[float]:
    if abs(factor - 1.0) < 0.001:
        return samples
    out = []
    pos = 0.0
    while int(pos) < len(samples) - 1:
        i = int(pos)
        frac = pos - i
        out.append(samples[i] * (1 - frac) + samples[i + 1] * frac)
        pos += factor
    return out


def find_files(staging: Path, *patterns: str) -> list[Path]:
    found = []
    for pat in patterns:
        found.extend(staging.rglob(pat))
    return sorted(set(found))


def pick_and_copy(src_files: list[Path], dest: Path, prefer: tuple[str, ...] = ()) -> bool:
    if not src_files:
        return False
    chosen = src_files[0]
    for p in prefer:
        for f in src_files:
            if p.lower() in f.name.lower():
                chosen = f
                break
    out = to_ogg(chosen, dest)
    return out.exists()


def build_footsteps(manifest_entries: dict):
    surfaces = {
        "grass": 180,
        "dirt": 140,
        "gravel": 220,
        "stone": 260,
        "road": 160,
        "wood": 200,
    }
    variants = ("low", "mid", "high")
    pitch = {"low": 0.92, "mid": 1.0, "high": 1.08}
    for surface, hz in surfaces.items():
        ids = []
        for vi, vname in enumerate(variants):
            for idx in range(3):
                wav = OUT / "_tmp" / f"{surface}_{vname}_{idx}.wav"
                raw = synth_footstep(hash((surface, vname, idx)) & 0xFFFF, hz * pitch[vname])
                write_wav(wav, raw)
                rel = f"sfx/footsteps/{surface}/{surface}_{vname}_{idx}"
                out = to_ogg(wav, OUT / f"{rel}.ogg")
                rel_path = out.relative_to(OUT).as_posix()
                fid = f"footstep_{surface}_{vname}_{idx}"
                manifest_entries[fid] = {
                    "file": rel_path,
                    "volume": 0.55,
                    "loop": False,
                    "group": f"footstep_{surface}",
                }
                ids.append(fid)
        manifest_entries[f"footstep_{surface}"] = {"group": ids, "volume": 0.55}


def build_procedural_ambient(manifest_entries: dict):
    loops = {
        "wind_soft": (8.0, synth_wind, 0.35),
        "wind_gust": (6.0, synth_wind, 0.45),
        "torch": (4.0, synth_torch, 0.4),
        "cave": (10.0, synth_cave, 0.5),
        "ember": (5.0, synth_ember, 0.25),
    }
    for name, (sec, fn, vol) in loops.items():
        wav = OUT / "_tmp" / f"{name}.wav"
        write_wav(wav, synth_loop(42, sec, fn))
        out = to_ogg(wav, OUT / f"sfx/ambient/{name}.ogg")
        manifest_entries[name] = {
            "file": out.relative_to(OUT).as_posix(),
            "volume": vol,
            "loop": True,
        }
    drip = OUT / "_tmp" / "drip.wav"
    write_wav(drip, synth_drip(99))
    out = to_ogg(drip, OUT / "sfx/ambient/drip.ogg")
    manifest_entries["drip"] = {"file": out.relative_to(OUT).as_posix(), "volume": 0.35, "loop": False}


def map_kenney_sfx(staging: Path, manifest_entries: dict):
    ui_map = {
        "ui_confirm": ("confirmation", "select", "click"),
        "ui_back": ("back", "close", "cancel"),
        "ui_examine": ("scroll", "tick", "switch"),
    }
    ogg_files = find_files(staging, "*.ogg", "*.wav", "*.mp3")
    for fid, prefs in ui_map.items():
        dest = OUT / f"sfx/ui/{fid}.ogg"
        if pick_and_copy(ogg_files, dest, prefs):
            manifest_entries[fid] = {"file": dest.relative_to(OUT).as_posix(), "volume": 0.6, "loop": False}

    game_map = {
        "pickup": ("coin", "pick", "drop"),
        "craft": ("craft", "anvil", "metal"),
        "stairs": ("door", "step", "footstep"),
        "battle_start": ("spell", "magic", "sword"),
        "hit": ("impact", "punch", "hit"),
        "dodge": ("whoosh", "swish", "swing"),
    }
    for fid, prefs in game_map.items():
        dest = OUT / f"sfx/game/{fid}.ogg"
        if pick_and_copy(ogg_files, dest, prefs):
            manifest_entries[fid] = {"file": dest.relative_to(OUT).as_posix(), "volume": 0.65, "loop": False}


def synth_music(seed: int, seconds: float, freqs: tuple[float, ...], mood: str = "calm") -> list[float]:
    rate = 44100
    n = int(rate * seconds)
    out = []
    for i in range(n):
        t = i / rate
        v = 0.0
        for j, f in enumerate(freqs):
            lfo = 0.5 + 0.5 * math.sin(t * (0.08 + j * 0.03) + seed)
            v += math.sin(2 * math.pi * f * t + seed * 0.1) * (0.12 / (j + 1)) * lfo
        if mood == "dark":
            v *= 0.7 + 0.3 * math.sin(t * 0.15)
        elif mood == "tense":
            v += math.sin(2 * math.pi * (freqs[0] * 1.5) * t) * 0.06 * (0.5 + 0.5 * math.sin(t * 2.5))
        # soft fade in/out for seamless loop feel
        edge = min(1.0, t / 2.0, (seconds - t) / 2.0)
        out.append(v * edge)
    return out


def build_procedural_music(manifest_entries: dict):
    tracks = {
        "music_title": ((130.81, 164.81, 196.0), "calm", 48.0, 0.4),
        "music_intro": ((110.0, 138.59, 164.81), "calm", 40.0, 0.35),
        "music_surface_day": ((146.83, 174.61, 220.0), "calm", 56.0, 0.42),
        "music_surface_night": ((98.0, 123.47, 146.83), "dark", 52.0, 0.38),
        "music_pepel": ((87.31, 103.83, 130.81), "dark", 44.0, 0.45),
        "music_dungeon": ((73.42, 92.5, 110.0), "dark", 60.0, 0.5),
        "music_battle": ((155.56, 185.0, 233.08), "tense", 36.0, 0.48),
    }
    for track_id, (freqs, mood, sec, vol) in tracks.items():
        wav = OUT / "_tmp" / f"{track_id}.wav"
        write_wav(wav, synth_music(hash(track_id) & 0xFFFF, sec, freqs, mood))
        out = to_ogg(wav, OUT / f"music/{track_id}.ogg")
        manifest_entries[track_id] = {
            "file": out.relative_to(OUT).as_posix(),
            "volume": vol,
            "loop": True,
            "music": True,
        }


def synth_blip(seed: int, freq: float, duration: float = 0.045) -> list[float]:
    rate = 44100
    n = int(rate * duration)
    out = []
    for i in range(n):
        t = i / rate
        env = math.exp(-t / (duration * 0.35))
        tone = math.sin(2 * math.pi * freq * t + seed * 0.01)
        out.append(tone * env * 0.55)
    return out


def build_voice_blips(manifest_entries: dict):
    voices = {
        "default": (440.0, 520.0),
        "elion": (290.0, 340.0),
        "elder": (175.0, 210.0),
        "whisper": (640.0, 760.0),
        "sorrow": (360.0, 430.0),
        "warden": (115.0, 145.0),
        "narrator": (400.0, 480.0),
    }
    for voice, (f0, f1) in voices.items():
        ids = []
        for vi, freq in enumerate((f0, f1)):
            wav = OUT / "_tmp" / f"voice_{voice}_{vi}.wav"
            write_wav(wav, synth_blip(hash((voice, vi)) & 0xFFFF, freq))
            fid = f"voice_{voice}_{vi}"
            out = to_ogg(wav, OUT / f"sfx/voices/{voice}_{vi}.ogg")
            rel = out.relative_to(OUT).as_posix()
            manifest_entries[fid] = {"file": rel, "volume": 0.32, "loop": False}
            ids.append(fid)
        manifest_entries[f"voice_{voice}"] = {"group": ids, "volume": 0.32}


def write_licenses():
    text = """# Audio licenses

## Kenney (CC0 1.0)
- Interface Sounds — https://kenney.nl/assets/interface-sounds
- Impact Sounds — https://kenney.nl/assets/impact-sounds
- RPG Audio — https://kenney.nl/assets/rpg-audio
- Credit optional: Kenney.nl

## FreePD (Public Domain)
- Music tracks from https://freepd.com — no attribution required

## Procedural fallbacks
- Footsteps, ambient loops (wind, torch, cave, ember, drip), and music tracks generated by
  `tools/prepare_audio.py` when source packs are unavailable or incomplete.
- Dialogue voice blips (typewriter text) are procedural per-character sets in `sfx/voices/`.
"""
    (OUT / "LICENSES.md").write_text(text, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    STAGING.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    for name, url in DOWNLOADS.items():
        zpath = STAGING / f"{name}.zip"
        if download(url, zpath):
            try:
                with zipfile.ZipFile(zpath) as zf:
                    zf.extractall(STAGING / name)
            except zipfile.BadZipFile:
                print(f"  bad zip {name}")

    manifest_entries: dict = {}
    build_footsteps(manifest_entries)
    build_procedural_ambient(manifest_entries)
    map_kenney_sfx(STAGING, manifest_entries)
    build_procedural_music(manifest_entries)
    build_voice_blips(manifest_entries)

    manifest = {"version": 1, "sounds": manifest_entries}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_licenses()

    tmp = OUT / "_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)

    count = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"Done: {count} files in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
