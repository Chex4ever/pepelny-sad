"""Tests for soul scan effects."""
from src.battle.soul_scan import apply_scan_effect, mercy_available


def test_unlock_mercy():
    flags: set[str] = set()
    log: list[str] = []
    apply_scan_effect({"type": "unlock_mercy"}, flags, set(), log)
    assert mercy_available(flags)
    assert any("Mercy" in line for line in log)


def test_unlock_recipe():
    discovered: set[str] = set()
    apply_scan_effect({"type": "unlock_recipe", "recipe": "ash_blade"}, set(), discovered, [])
    assert "ash_blade" in discovered


def test_reveal_pattern():
    flags: set[str] = set()
    apply_scan_effect({"type": "reveal_pattern", "pattern": "rain"}, flags, set(), [])
    assert "reveal_rain" in flags
