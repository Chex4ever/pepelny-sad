"""Roll NPC character specs."""
from __future__ import annotations

import random

from src.characters.loader import load_races_catalog
from src.characters.spec import CharacterSpec


def roll_npc_spec(
    seed: int,
    *,
    race_pool: list[str] | None = None,
    age_years: float | None = None,
) -> CharacterSpec:
    rng = random.Random(seed)
    catalog = load_races_catalog()
    pool = race_pool or sorted(catalog.keys())
    race_id = pool[rng.randrange(len(pool))]
    race = catalog[race_id]
    if age_years is None:
        age_years = rng.uniform(race.age_thresholds.child_max + 1, race.age_thresholds.adult_max)
    return CharacterSpec(
        race_id=race_id,
        seed=rng.randint(0, 2**31 - 1),
        age_years=age_years,
    )
