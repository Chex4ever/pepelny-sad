"""Headless PNG export for dia_scale scenes."""
from __future__ import annotations

import os

import pygame

from src.prototype.dia_scale.cross_section import project_xz, project_yz, slice_xz, slice_yz
from src.prototype.dia_scale.display_scale import PRESET_NORMAL, DisplayPreset, WINDOW_PX_W
from src.prototype.dia_scale.renderer import CharGridRenderer
from src.prototype.dia_scale.section_renderer import SectionRenderer, blit_split
from src.prototype.dia_scale.slice_view import SliceViewMode
from src.prototype.dia_scale.tree_voxel_gen import project_tree_at_z, project_tree_up_to_z
from src.prototype.dia_scale.world_grid import WorldGrid


def export_scene_png(
    grid: WorldGrid,
    path: str,
    *,
    focus_cx: int | None = None,
    focus_cy: int | None = None,
    rotation: int = 0,
    preset: DisplayPreset | None = None,
    tree_model=None,
    section_plane: str = "yz",
    section_coord: int | None = None,
    top_slice_z: int | None = None,
    slice_view: SliceViewMode = "slice",
) -> str:
    bounds = grid.floor_bounds()
    if bounds is None:
        raise ValueError("empty grid")
    min_x, min_y, max_x, max_y = bounds
    if focus_cx is None:
        focus_cx = (min_x + max_x) // 2
    if focus_cy is None:
        focus_cy = (min_y + max_y) // 2

    p = preset or PRESET_NORMAL
    renderer = CharGridRenderer(preset=p)
    renderer.camera.focus_cx = focus_cx
    renderer.camera.focus_cy = focus_cy
    renderer.camera.rotation = rotation % 4
    top_w = WINDOW_PX_W // 2

    if tree_model is not None:
        ax, ay = tree_model.anchor_x, tree_model.anchor_y
        coord = section_coord if section_coord is not None else ax
        z_cut = top_slice_z if top_slice_z is not None else tree_model.max_z() // 2
        render_kw: dict = {
            "hud_lines": renderer.default_hud(grid),
            "viewport_w": top_w,
            "viewport_cx": top_w // 2,
        }
        if slice_view != "off":
            render_kw["z_cut"] = z_cut
            if slice_view == "slice":
                render_kw["z_cut_solids"] = project_tree_at_z(tree_model, z_cut)
            else:
                render_kw["z_cut_solids"] = project_tree_up_to_z(tree_model, z_cut)
            render_kw["section_cut"] = (section_plane, coord)
        top = renderer.render(grid, **render_kw)
        if slice_view == "off":
            if section_plane == "xz":
                section = project_xz(tree_model)
                title = "XZ projection"
            else:
                section = project_yz(tree_model)
                title = "YZ projection"
        elif section_plane == "xz":
            section = slice_xz(tree_model, coord)
            title = f"XZ section Y={coord}"
        else:
            section = slice_yz(tree_model, coord)
            title = f"YZ section X={coord}"
        sec_r = SectionRenderer(preset=p, panel_w=top_w)
        section_surf = sec_r.render(
            section, title=title, z_cut=z_cut if slice_view != "off" else None, z_cut_mode=slice_view
        )
        out = pygame.Surface((WINDOW_PX_W, top.get_height()))
        blit_split(out, top, section_surf, top_w=top_w)
        surf = out
    else:
        top = renderer.render(grid, hud_lines=renderer.default_hud(grid))
        surf = top

    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pygame.image.save(surf, path)
    return path
