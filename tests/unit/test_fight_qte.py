"""Tests for fight QTE."""
from src.battle.fight_qte import FightQTE


def test_blade_has_narrower_window_than_staff():
    blade = FightQTE("blade")
    staff = FightQTE("staff")
    assert (blade.window_end - blade.window_start) < (staff.window_end - staff.window_start)


def test_try_hit_in_window():
    qte = FightQTE("staff")
    qte.start()
    qte.cursor = 0.45
    assert qte.try_hit()
    assert qte.result is True


def test_try_hit_outside_window():
    qte = FightQTE("blade")
    qte.start()
    qte.cursor = 0.1
    assert not qte.try_hit()
    assert qte.result is False
