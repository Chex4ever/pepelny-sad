"""Soul Scan (Act) effects."""
from __future__ import annotations


def apply_scan_effect(effect: dict, scan_flags: set, discovered_recipes: set, log: list) -> None:
    if not effect:
        return
    et = effect.get("type")
    if et == "unlock_mercy":
        scan_flags.add("unlock_mercy")
        log.append("[SCAN] Mercy стал возможен.")
    elif et == "unlock_recipe":
        rid = effect.get("recipe")
        if rid:
            discovered_recipes.add(rid)
            log.append(f"[SCAN] Открыт рецепт: {rid}")
    elif et == "reveal_pattern":
        pat = effect.get("pattern", "")
        scan_flags.add(f"reveal_{pat}")
        log.append(f"[SCAN] Паттерн «{pat}» — подсказка получена.")


def mercy_available(scan_flags: set) -> bool:
    return "unlock_mercy" in scan_flags
