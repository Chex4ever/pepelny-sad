"""Smoke tests for biome/meadow preview tools and iso_preview (no interactive window)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def preview_env(monkeypatch):
    """Headless pygame + data paths."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("PEPELNY_RENDER", "iso")
    from src.constants import init_paths

    init_paths(str(ROOT))
    import pygame

    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def biome_viewer():
    return _load_script("biome_viewer.py")


@pytest.mark.unit
def test_biome_viewer_prepare_patch_all_biomes(preview_env, biome_viewer):
    from src.data.art_loader import load_biomes

    for bid in load_biomes():
        _chunk, queue, stats, _holes = biome_viewer.prepare_patch(
            0,
            0,
            10,
            10,
            4242,
            bid,
            forced=True,
            trees=False,
            render_mode="iso",
        )
        assert stats.biome_id == bid
        assert stats.w == 10 and stats.h == 10
        assert len(queue) >= 100
        floor = [t for t in queue if t[3] == 0.0]
        assert len(floor) >= 100


@pytest.mark.unit
def test_biome_viewer_climate_mode(preview_env, biome_viewer):
    _chunk, queue, stats, _holes = biome_viewer.prepare_patch(
        50,
        50,
        8,
        8,
        99,
        "meadow",
        forced=False,
        trees=False,
        render_mode="iso",
    )
    assert stats.biome_id == "climate"
    assert len(queue) > 0


@pytest.mark.unit
def test_biome_viewer_trees_add_solids(preview_env, biome_viewer):
    _chunk, queue, stats, _holes = biome_viewer.prepare_patch(
        0,
        0,
        12,
        12,
        777,
        "ashen_forest",
        forced=True,
        trees=True,
        render_mode="iso",
    )
    assert stats.trees is True
    sids = [t[4] for t in queue]
    assert any("trunk" in sid or "canopy" in sid for sid in sids)


@pytest.mark.unit
def test_biome_viewer_export_all_writes_artifacts(preview_env, biome_viewer, tmp_path):
    from src.data.art_loader import load_biomes

    code = biome_viewer.run_export_all(str(tmp_path), seed=4242, size=8, render_mode="iso")
    assert code == 0
    report = tmp_path / "report_s4242.json"
    assert report.is_file()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["render_path"] == "iso"
    assert set(data["biomes"]) == set(load_biomes().keys())
    for bid in load_biomes():
        pngs = list(tmp_path.glob(f"biome_{bid}_*.png"))
        assert pngs, f"missing png for {bid}"


@pytest.mark.unit
def test_prepare_patch_does_not_break_gpu_context(monkeypatch):
    from src.constants import init_paths, COLOR_BG

    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    init_paths(str(ROOT))
    import pygame

    from src.tools.iso_preview import OverworldPreview

    pygame.init()
    biome_viewer = _load_script("biome_viewer.py")
    preview = OverworldPreview("gpu")
    try:
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        biome_viewer.prepare_patch(
            0, 0, 8, 8, 1, "meadow", forced=True, trees=False, render_mode="gpu"
        )
        ctx = preview._presenter._gpu.ctx
        ctx.clear(COLOR_BG[0] / 255, COLOR_BG[1] / 255, COLOR_BG[2] / 255)
        sample = bytes(ctx.screen.read(components=3))
        assert sample[0:3] == bytes(COLOR_BG)
    finally:
        preview.release()


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_gpu_iso_footprint_not_stretched_glyphs(monkeypatch):
    """Footprint fill must be solid biome tint, not scaled iso_tile_fill 'yy' glyphs."""
    import struct

    from src.constants import init_paths

    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    init_paths(str(ROOT))
    import pygame

    from src.tools.iso_preview import OverworldPreview, build_surface_draw_queue

    pygame.init()
    preview = OverworldPreview("gpu")
    try:
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        biome_viewer = _load_script("biome_viewer.py")
        chunk = biome_viewer.generate_patch(
            0, 0, 8, 8, 1, forced_biome="meadow", trees=False
        )
        queue = build_surface_draw_queue(chunk, 0, 0, 8, 8)
        iso = preview._presenter._iso
        b = iso._builder
        b.clear()
        item = next(t for t in queue if t[3] == 0.0)
        _, wx, wy, z_m, sid, fg, bg, light, fog = item
        ax, ay = iso._projector.world_to_screen(wx, wy, z_m, focus_wx=4, focus_wy=4)
        iso._stamp_stencil(
            b, ax, ay, sid, fg=fg, bg=bg, light=light, fog=fog, expand_footprint=True
        )
        data = b.tobytes()
        stride = 15 * 4
        solid_quads = sum(
            1
            for i in range(0, len(data), stride)
            if struct.unpack("4f", data[i + stride - 16 : i + stride])[0] < -0.5
        )
        assert solid_quads >= 6, f"expected per-cell footprint fills, got {solid_quads}"
        iso.draw(queue, focus_wx=4, focus_wy=4)
        data = bytes(iso._gpu.ctx.screen.read(components=3))
        green = sum(
            1
            for y in range(0, preview.pixel_h, 12)
            for x in range(0, preview.pixel_w, 12)
            if data[(y * preview.pixel_w + x) * 3 + 1] > 40
        )
        assert green > 20, f"expected tinted meadow tiles, got {green} green samples"
    finally:
        preview.release()


@pytest.mark.unit
def test_preview_gpu_ui_buffer_sparse(preview_env):
    from src.tools.iso_preview import clear_preview_ui_buffer, draw_hud_lines
    from src.render.screen_buffer import ScreenBuffer

    buf = ScreenBuffer(20, 10)
    clear_preview_ui_buffer(buf)
    assert all(a < 8 for a in buf.bg_a)
    draw_hud_lines(buf, ["HUD line"])
    hud_cells = sum(1 for ch in buf.chars if ch != " ")
    assert 0 < hud_cells < 50


@pytest.mark.unit
def test_overworld_preview_mode_label_and_cpu_capture(preview_env):
    from src.data.art_loader import load_biomes
    from src.tools.iso_preview import OverworldPreview, build_surface_draw_queue

    preview = OverworldPreview("iso")
    assert preview.mode == "iso"
    assert "iso" in preview.mode_label.lower() or "CPU" in preview.mode_label

    biome_viewer = _load_script("biome_viewer.py")
    chunk = biome_viewer.generate_patch(
        0, 0, 8, 8, 1, forced_biome="meadow", trees=False
    )
    queue = build_surface_draw_queue(chunk, 0, 0, 8, 8)
    surf = preview.capture(queue, focus_wx=4, focus_wy=4)
    assert surf.get_width() > 0 and surf.get_height() > 0
    preview.release()


@pytest.mark.unit
def test_iso_preview_build_queue_matches_game_z_rules(preview_env):
    from src.tools.iso_preview import build_surface_draw_queue
    from src.world.tree_generator import build_tree_solids, roll_tree_params, tree_anchor
    from src.data.art_loader import load_biomes
    from src.world.chunk import Chunk

    chunk = Chunk(0, 0)
    wx, wy = 4, 4
    lx, ly = wx, wy
    params = roll_tree_params(load_biomes()["meadow"], 1, wx, wy)
    chunk.structure_anchors.append(tree_anchor(wx, wy, load_biomes()["meadow"], 1))
    for dx, dy, solid in build_tree_solids(params):
        chunk.add_solid(lx + dx, ly + dy, solid)

    queue = build_surface_draw_queue(chunk, 0, 0, 8, 8)
    canopy = [t for t in queue if "canopy" in t[4]]
    trunk = [t for t in queue if "trunk" in t[4]]
    assert canopy and trunk
    assert any(t[1] == wx and t[2] == wy for t in canopy)
    assert trunk[0][1] == wx and trunk[0][2] == wy


@pytest.mark.unit
def test_parallel_chunk_generate_smoke(preview_env):
    from src.world.surface_gen import generate_chunk_isolated
    from src.core.parallel_load import generate_chunks_parallel
    from src.world.world_fields import init_world_fields

    init_world_fields(42)
    single = generate_chunks_parallel([(0, 0)], 42)
    assert (0, 0) in single

    multi = generate_chunks_parallel([(0, 0), (1, 0), (0, 1)], 42)
    assert len(multi) == 3


@pytest.mark.unit
def test_meadow_preview_prepare_patch_smoke(preview_env, biome_viewer):
    _chunk, queue, stats, _holes = biome_viewer.prepare_patch(
        0,
        0,
        14,
        14,
        4242,
        "meadow",
        forced=True,
        trees=False,
        render_mode="iso",
    )
    assert stats.biome_id == "meadow"
    assert len(queue) >= 14 * 14


@pytest.mark.unit
def test_tree_viewer_module_imports(preview_env):
    _load_script("tree_viewer.py")
    from src.world.tree_generator import build_tree_solids, roll_tree_params
    from src.data.art_loader import load_biomes

    solids = build_tree_solids(roll_tree_params(load_biomes()["meadow"], 42, 0, 0))
    assert len(solids) >= 2


@pytest.mark.unit
@pytest.mark.parametrize(
    "argv",
    [
        ["biome_viewer.py", "--export", "meadow", "--seed", "1", "--size", "8", "--render", "iso"],
        ["biome_viewer.py", "--export-all", "--seed", "2", "--size", "6", "--render", "iso"],
    ],
)
def test_scripts_cli_exit_zero(preview_env, tmp_path, argv):
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["PEPELNY_RENDER"] = "iso"
    cmd = [sys.executable, str(SCRIPTS / argv[0])]
    if "--out-dir" not in argv:
        cmd += ["--out-dir", str(tmp_path / argv[0].replace(".py", ""))]
    cmd += argv[1:]
    if "--export-all" in argv:
        out = tmp_path / "export_all"
        out.mkdir(parents=True, exist_ok=True)
        cmd += ["--out-dir", str(out)]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_overworld_preview_gpu_present_hud_smoke(monkeypatch):
    from src.constants import init_paths
    from src.tools.iso_preview import OverworldPreview, build_surface_draw_queue

    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    monkeypatch.delenv("SDL_AUDIODRIVER", raising=False)
    init_paths(str(ROOT))
    import pygame

    pygame.init()
    try:
        biome_viewer = _load_script("biome_viewer.py")
        preview = OverworldPreview("gpu")
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        chunk = biome_viewer.generate_patch(
            0, 0, 8, 8, 3, forced_biome="meadow", trees=False
        )
        queue = build_surface_draw_queue(chunk, 0, 0, 8, 8)
        preview.present(
            queue,
            focus_wx=4,
            focus_wy=4,
            hud_lines=["smoke hud", "line2"],
        )
        assert preview._presenter._ui.last_quad_count < 500
        surf = preview.capture(queue, focus_wx=4, focus_wy=4)
        assert surf.get_width() == preview.pixel_w
        preview.release()
    finally:
        pygame.quit()


@pytest.mark.unit
def test_cpu_render_queue_draws_sprite(preview_env):
    from src.tools.iso_preview import build_object_preview_queue, render_queue_cpu

    queue = build_object_preview_queue("sprite:player", wx=10, wy=10)
    buf = render_queue_cpu(queue, focus_wx=10, focus_wy=10, buf_w=40, buf_h=30)
    chars = set()
    for y in range(buf.height):
        for x in range(buf.width):
            ch = buf.chars[buf._idx(x, y)]
            if ch != " ":
                chars.add(ch)
    assert "@" in chars


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_gpu_player_sprite_not_upside_down(monkeypatch):
    """Head (@) must stamp above legs (/) on screen — per-glyph atlas UV rows."""
    import struct

    from src.constants import init_paths

    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    init_paths(str(ROOT))
    import pygame

    from src.render.tile_stencil import load_sprite
    from src.tools.iso_preview import OverworldPreview

    pygame.init()
    preview = OverworldPreview("gpu")
    try:
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        iso = preview._presenter._iso
        b = iso._builder
        b.clear()
        iso._stamp_stencil(
            b,
            50,
            30,
            "sprite:player",
            fg=(255, 220, 120),
            bg=(8, 8, 18),
            light=1.0,
            fog=0,
            expand_footprint=False,
        )
        st = load_sprite("player")
        head = next(g for g in st.glyphs if g.ch == "@")
        foot = next(g for g in st.glyphs if g.dy == 0 and g.ch == "/")
        stride = 15 * 4
        data = b.tobytes()
        head_y = foot_y = None
        for i in range(0, len(data), stride):
            x0 = struct.unpack("f", data[i : i + 4])[0]
            y0 = struct.unpack("f", data[i + 4 : i + 8])[0]
            uvx = struct.unpack("4f", data[i + stride - 16 : i + stride])[0]
            if uvx < -0.5:
                continue
            cx = int(x0 // 10)
            cy = int(y0 // 16)
            if (cx, cy) == (50 + head.dx, 30 + head.dy):
                head_y = y0
            if (cx, cy) == (50 + foot.dx, 30 + foot.dy):
                foot_y = y0
        assert head_y is not None and foot_y is not None
        assert head_y < foot_y, f"head y={head_y} should be above foot y={foot_y}"
    finally:
        preview.release()
        pygame.quit()


@pytest.mark.unit
def test_object_viewer_prepare_player(preview_env):
    object_viewer = _load_script("object_viewer.py")
    queue, meta = object_viewer.prepare_object_scene(
        "sprite:player",
        wx0=0,
        wy0=0,
        patch=8,
        seed=1,
        floor_biome="meadow",
        show_floor=True,
    )
    assert meta["label"] == "player"
    assert any(t[4] == "sprite:player" for t in queue)
    assert any(t[3] == 0.0 for t in queue)


@pytest.mark.unit
def test_cpu_render_queue_draws_sprite(preview_env):
    from src.constants import SCREEN_H, SCREEN_W
    from src.tools.iso_preview import build_object_preview_queue, render_queue_cpu

    queue = build_object_preview_queue("sprite:player", wx=10, wy=10)
    buf = render_queue_cpu(
        queue, focus_wx=10, focus_wy=10, buf_w=SCREEN_W, buf_h=SCREEN_H
    )
    chars = set()
    for y in range(buf.height):
        for x in range(buf.width):
            ch = buf.chars[buf._idx(x, y)]
            if ch != " ":
                chars.add(ch)
    assert "@" in chars


@pytest.mark.unit
@pytest.mark.skipif(
    not __import__("src.render.gpu.context", fromlist=["gl_available"]).gl_available(),
    reason="No OpenGL",
)
def test_gpu_player_sprite_not_upside_down(monkeypatch):
    """Head (@) must stamp above legs (/) on screen — per-glyph atlas UV rows."""
    import struct

    from src.constants import ENTITY_DRAW_Z_M, init_paths

    monkeypatch.delenv("SDL_VIDEODRIVER", raising=False)
    init_paths(str(ROOT))
    import pygame

    from src.render.tile_stencil import load_sprite
    from src.tools.iso_preview import OverworldPreview

    pygame.init()
    preview = OverworldPreview("gpu")
    try:
        if not preview.available_gpu:
            pytest.skip("GpuPresenter unavailable")
        iso = preview._presenter._iso
        b = iso._builder
        b.clear()
        iso._stamp_stencil(
            b,
            50,
            30,
            "sprite:player",
            fg=(255, 220, 120),
            bg=(8, 8, 18),
            light=1.0,
            fog=0,
            expand_footprint=False,
        )
        st = load_sprite("player")
        head = next(g for g in st.glyphs if g.ch == "@")
        foot = next(g for g in st.glyphs if g.dy == 0 and g.ch == "/")
        stride = 15 * 4
        data = b.tobytes()
        y_by_glyph: dict[tuple[int, int], float] = {}
        for i in range(0, len(data), stride):
            y0 = struct.unpack("f", data[i + 4 : i + 8])[0]
            uvx = struct.unpack("4f", data[i + stride - 16 : i + stride])[0]
            if uvx < -0.5:
                continue
            cx = int(y0)  # wrong - need x from first float
        # parse quads: pos is x0,y0 at i, i+4
        head_y = foot_y = None
        for i in range(0, len(data), stride):
            x0 = struct.unpack("f", data[i : i + 4])[0]
            y0 = struct.unpack("f", data[i + 4 : i + 8])[0]
            uvx = struct.unpack("4f", data[i + stride - 16 : i + stride])[0]
            if uvx < -0.5:
                continue
            cx = int(x0 // 10)
            cy = int(y0 // 16)
            if (cx, cy) == (50 + head.dx, 30 + head.dy):
                head_y = y0
            if (cx, cy) == (50 + foot.dx, 30 + foot.dy):
                foot_y = y0
        assert head_y is not None and foot_y is not None
        assert head_y < foot_y, f"head y={head_y} should be above foot y={foot_y}"
    finally:
        preview.release()
        pygame.quit()


@pytest.mark.unit
def test_object_viewer_prepare_player(preview_env):
    object_viewer = _load_script("object_viewer.py")
    queue, meta = object_viewer.prepare_object_scene(
        "sprite:player",
        wx0=0,
        wy0=0,
        patch=8,
        seed=1,
        floor_biome="meadow",
        show_floor=True,
    )
    assert meta["label"] == "player"
    assert any(t[4] == "sprite:player" for t in queue)
    assert any(t[3] == 0.0 for t in queue)
