"""Shadow map and sun direction."""
from __future__ import annotations

from src.render.shadow_casters import column_caster_height
from src.render.shadow_map import ShadowCaster, ShadowMap
from src.world.column import Column, Solid
from src.world.lighting import sun_shadow_vector


def test_sun_shadow_vector_surface_noon_shorter():
    _, _, scale_noon = sun_shadow_vector(120, "surface")
    _, _, scale_dusk = sun_shadow_vector(200, "surface")
    assert scale_noon < scale_dusk


def test_shadow_map_darkens_tiles_ahead():
    sm = ShadowMap(10, 10, shadow_floor=0.4)
    sm.apply_all(
        [ShadowCaster(5, 5, 4.0)],
        1,
        1,
        length_scale=0.8,
    )
    assert sm.get(5, 5) == 1.0
    assert sm.get(6, 6) < 0.85
    assert sm.get(7, 7) < sm.get(6, 6)


def test_column_caster_height_tree_trunk():
    col = Column()
    col.add_solid(
        Solid(0.0, 3.0, blocks_los=True, stencil_id="tree_trunk_slim")
    )
    assert column_caster_height(col) >= 3.0
