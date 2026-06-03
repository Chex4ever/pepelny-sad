"""Pattern registry (re-export from bullets)."""
from src.battle.bullets import Bullet, BulletPattern, check_hit

PATTERN_IDS = ["rain", "sides", "spiral"]

__all__ = ["Bullet", "BulletPattern", "check_hit", "PATTERN_IDS"]
