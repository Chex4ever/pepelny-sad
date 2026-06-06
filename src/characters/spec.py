"""Character instance spec."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Sex = Literal["male", "female", "neutral"]


@dataclass(frozen=True)
class CharacterSpec:
    race_id: str
    seed: int
    age_years: float
    sex: Sex = "neutral"
    equipment: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "race_id": self.race_id,
            "seed": int(self.seed),
            "age_years": float(self.age_years),
            "sex": self.sex,
            "equipment": {k: v for k, v in self.equipment.items() if v},
        }

    @classmethod
    def from_dict(cls, d: dict) -> CharacterSpec:
        return cls(
            race_id=d["race_id"],
            seed=int(d["seed"]),
            age_years=float(d["age_years"]),
            sex=d.get("sex", "neutral"),
            equipment=dict(d.get("equipment", {})),
        )

    def with_equipment(self, slot: str, item_id: str | None) -> CharacterSpec:
        eq = dict(self.equipment)
        if item_id:
            eq[slot] = item_id
        else:
            eq.pop(slot, None)
        return CharacterSpec(
            race_id=self.race_id,
            seed=self.seed,
            age_years=self.age_years,
            sex=self.sex,
            equipment=eq,
        )
