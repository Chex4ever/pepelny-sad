"""Unit tests for dia_scale generators and test_2x1_dia script."""
from __future__ import annotations

import importlib.util
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
def dia_env(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    from src.constants import init_paths

    init_paths(str(ROOT))
    import pygame

    pygame.init()
    yield
    pygame.quit()


@pytest.mark.unit
def test_meadow_no_internal_gaps(dia_env):
    from src.prototype.dia_scale.meadow_gen import generate_meadow
    from src.prototype.dia_scale.tessellation import analyze_floor_coverage

    nx, ny = 12, 12
    generate_meadow(seed=1, nx=nx, ny=ny)
    stats = analyze_floor_coverage(nx, ny)
    assert stats.internal_gaps == 0
    assert stats.coverage_pct >= 90.0


@pytest.mark.unit
def test_meadow_coverage_stable_under_view_rotation(dia_env):
    from src.prototype.dia_scale.meadow_gen import generate_meadow
    from src.prototype.dia_scale.tessellation import analyze_floor_coverage, world_to_view

    nx, ny = 10, 10
    grid = generate_meadow(seed=99, nx=nx, ny=ny)
    stats = analyze_floor_coverage(nx, ny)
    assert stats.internal_gaps == 0

    focus = (nx, ny)
    view_counts = []
    for rot in range(4):
        seen = set()
        for (cx, cy) in grid.floor:
            vx, vy = world_to_view(cx, cy, focus[0], focus[1], rot)
            seen.add((vx, vy))
        view_counts.append(len(seen))
    assert len(set(view_counts)) == 1


@pytest.mark.unit
def test_meadow_export_png(dia_env, tmp_path):
    from src.prototype.dia_scale.export_png import export_scene_png
    from src.prototype.dia_scale.scene import build_scene

    grid = build_scene(seed=7, nx=8, ny=8, trees=False, player=False)
    path = str(tmp_path / "meadow.png")
    export_scene_png(grid, path)
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 100


@pytest.mark.unit
def test_tree_solids_height_and_rotation_invariant(dia_env):
    from src.prototype.dia_scale.meadow_gen import generate_meadow
    from src.prototype.dia_scale.tessellation import world_to_view
    from src.prototype.dia_scale.tree_gen import generate_trees

    nx, ny = 12, 12
    grid = generate_meadow(seed=42, nx=nx, ny=ny)
    generate_trees(grid, seed=42, nx=nx, ny=ny, tree_density=0.25, bush_density=0.1)

    trunks = [s for s in grid.solids if s.kind == "trunk"]
    canopies = [s for s in grid.solids if s.kind == "canopy"]
    assert trunks
    assert canopies
    for t in trunks:
        assert t.z_max > t.z_min

    world_cells = frozenset((s.cx, s.cy) for s in grid.solids)
    focus = (nx, ny)
    for rot in range(4):
        mapped = frozenset(
            world_to_view(cx, cy, focus[0], focus[1], rot) for cx, cy in world_cells
        )
        assert len(mapped) == len(world_cells)


@pytest.mark.unit
def test_player_height_18_chars(dia_env):
    from src.characters.appearance import default_appearance
    from src.characters.bake import bake_voxel_model
    from src.prototype.dia_scale.constants import PLAYER_HEIGHT_CHARS
    from src.prototype.dia_scale.entity_gen import (
        place_player,
        player_footprint_cells,
        player_sprite_rows,
    )
    from src.prototype.dia_scale.meadow_gen import generate_meadow

    rows = player_sprite_rows()
    assert len(rows) >= PLAYER_HEIGHT_CHARS - 3
    assert len(rows) <= PLAYER_HEIGHT_CHARS + 4
    model = bake_voxel_model(default_appearance())
    zs = [z for _x, _y, z in model.voxels]
    assert max(zs) - min(zs) + 1 >= PLAYER_HEIGHT_CHARS - 2
    grid = generate_meadow(seed=1, nx=6, ny=6)
    ent = place_player(grid, feet_cx=5, feet_cy=5)
    assert ent.feet_cx == 5 and ent.feet_cy == 5
    fp = player_footprint_cells(5, 5)
    assert len(fp) > 10
    assert grid.has_floor(5, 5)


@pytest.mark.unit
def test_test_2x1_dia_script_cli_exit_zero(dia_env, tmp_path):
    out = tmp_path / "out.png"
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "test_2x1_dia.py"),
            "--export",
            "--seed",
            "1",
            "--nx",
            "8",
            "--ny",
            "8",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.mark.unit
def test_export_all_rotations(dia_env, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "test_2x1_dia.py"),
            "--export-all-rotations",
            "--seed",
            "2",
            "--nx",
            "6",
            "--ny",
            "6",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    debug = ROOT / "assets" / "debug"
    for rot in range(4):
        assert (debug / f"test_2x1_dia_scene_rot{rot}.png").is_file()


@pytest.mark.unit
def test_scale_anisotropic(dia_env):
    from src.prototype.dia_scale.constants import (
        PLAYER_HEIGHT_M,
        PLAYER_HEIGHT_TILES,
        TILE_XY_M,
        TILE_Z_M,
        TREE_HEIGHT_TILES,
    )

    assert TILE_XY_M == 0.2
    assert TILE_Z_M == 0.1
    assert TREE_HEIGHT_TILES * TILE_Z_M == 10.0
    assert PLAYER_HEIGHT_TILES * TILE_Z_M == pytest.approx(1.8)
    assert PLAYER_HEIGHT_M == pytest.approx(1.8)


@pytest.mark.unit
def test_voxel_tree_height_100(dia_env):
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=42, species_id="pine", age_years=80)
    assert model.max_z() >= 50


@pytest.mark.unit
def test_voxel_trunk_base_width_4(dia_env):
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=7, species_id="oak", age_years=150)
    assert model.trunk_width_at_z(0) >= 3


@pytest.mark.unit
def test_voxel_trunk_spine_continuous(dia_env):
    from src.prototype.dia_scale.constants import VOXEL_TRUNK
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=4242, species_id="oak", age_years=120)
    ax, ay = model.anchor_x, model.anchor_y
    mid = model.max_z() // 3
    missing = [z for z in range(mid) if model.voxels.get((ax, ay, z)) != VOXEL_TRUNK]
    assert len(missing) < mid * 0.15, f"too many trunk gaps: {len(missing)}/{mid}"


@pytest.mark.unit
def test_voxel_has_branches(dia_env):
    from src.prototype.dia_scale.constants import VOXEL_BRANCH, VOXEL_LEAF
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=99, height_tiles=100)
    counts = model.kind_counts()
    assert counts.get(VOXEL_BRANCH, 0) > 0
    assert counts.get(VOXEL_LEAF, 0) > 0
    assert model.branch_count > 0


@pytest.mark.unit
def test_cross_section_nonempty(dia_env):
    from src.prototype.dia_scale.constants import VOXEL_BRANCH, VOXEL_LEAF, VOXEL_TRUNK
    from src.prototype.dia_scale.cross_section import section_kinds, slice_yz
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=11, height_tiles=100)
    section = slice_yz(model, model.anchor_x)
    kinds = section_kinds(section)
    assert VOXEL_TRUNK in kinds
    assert VOXEL_BRANCH in kinds or VOXEL_LEAF in kinds


@pytest.mark.unit
def test_project_yz_wider_than_single_slice(dia_env):
    from src.prototype.dia_scale.cross_section import project_yz, slice_yz
    from src.prototype.dia_scale.tree_voxel_gen import generate_voxel_tree

    model = generate_voxel_tree(seed=11, height_tiles=100)
    yz_slice = slice_yz(model, model.anchor_x)
    yz_proj = project_yz(model)
    assert len(yz_proj.cells) >= len(yz_slice.cells)


@pytest.mark.unit
def test_slice_view_cycle(dia_env):
    from src.prototype.dia_scale.slice_view import cycle_slice_view_mode

    assert cycle_slice_view_mode("slice") == "rear"
    assert cycle_slice_view_mode("rear") == "off"
    assert cycle_slice_view_mode("off") == "slice"


@pytest.mark.unit
def test_display_preset_changes_visible_chars(dia_env):
    from src.prototype.dia_scale.display_scale import PRESET_COMPACT, PRESET_NORMAL, visible_chars

    w_n, h_n = visible_chars(PRESET_NORMAL)
    w_c, h_c = visible_chars(PRESET_COMPACT)
    assert w_c >= w_n
    assert h_c >= h_n


@pytest.mark.unit
def test_tree_mode_export(dia_env):
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "test_2x1_dia.py"),
            "--mode",
            "tree",
            "--export",
            "--seed",
            "5",
            "--nx",
            "8",
            "--ny",
            "8",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (ROOT / "assets" / "debug" / "test_2x1_dia_tree_section.png").is_file()
