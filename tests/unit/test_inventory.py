"""Tests for inventory."""
from src.progression.inventory import Inventory


def test_add_and_count_stacks():
    inv = Inventory(4)
    assert inv.add("grey_herb", 3, stack_max=20) == 0
    assert inv.count("grey_herb") == 3


def test_add_respects_capacity():
    inv = Inventory(2)
    assert inv.add("a", 1) == 0
    assert inv.add("b", 1) == 0
    leftover = inv.add("c", 1)
    assert leftover == 1
    assert inv.count("c") == 0


def test_remove_partial_stack():
    inv = Inventory(4)
    inv.add("ash_clump", 5, stack_max=30)
    assert inv.remove("ash_clump", 2)
    assert inv.count("ash_clump") == 3


def test_has_checks_total_across_slots():
    inv = Inventory(4)
    inv.add("x", 2, stack_max=2)
    inv.add("x", 2, stack_max=2)
    assert inv.has("x", 4)
    assert not inv.has("x", 5)
