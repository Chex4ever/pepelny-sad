"""Regression: updater must not run from git checkout (not frozen)."""
from __future__ import annotations

import pytest

from src.updater.manager import is_frozen, maybe_update


@pytest.mark.regression
def test_updater_skipped_when_not_frozen(monkeypatch):
    monkeypatch.setattr("src.updater.manager.is_frozen", lambda: False)

    class FailProvider:
        def fetch_manifest(self):
            raise AssertionError("must not fetch when not frozen")

    assert maybe_update(FailProvider()) is False


@pytest.mark.regression
def test_is_frozen_false_in_dev():
    assert is_frozen() is False
