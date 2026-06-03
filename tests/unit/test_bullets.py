"""Tests for bullet patterns."""
from src.battle.bullets import Bullet, BulletPattern, check_hit


def test_rain_pattern_spawns_bullets():
    pattern = BulletPattern("rain", 30, 15)
    for _ in range(20):
        pattern.update()
    assert len(pattern.active_bullets()) > 0


def test_check_hit_detects_overlap():
    bullets = [Bullet(5.0, 5.0, 0, 0)]
    assert check_hit(5.0, 5.0, 0.5, bullets)


def test_check_hit_misses_far_bullet():
    bullets = [Bullet(20.0, 20.0, 0, 0)]
    assert not check_hit(1.0, 1.0, 0.5, bullets)


def test_pattern_completes_after_duration():
    pattern = BulletPattern("sides", 20, 10)
    pattern.duration = 10
    for _ in range(12):
        pattern.update()
    assert pattern.done
