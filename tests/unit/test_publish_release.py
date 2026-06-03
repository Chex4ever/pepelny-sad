"""Tests for GitHub release publish helpers."""
from tools.publish_github_release import is_primary_asset


def test_primary_assets_detection():
    assert is_primary_asset("manifest-win-x64.json")
    assert is_primary_asset("manifest-linux-x64.json")
    assert is_primary_asset("pepelny-sad-0.2.9-win-x64-setup.exe")
    assert is_primary_asset("pepelny-sad-0.2.9-linux-x64.tar.gz")
    assert not is_primary_asset("win-x64--pepelny-sad.exe")
    assert not is_primary_asset("linux-x64--_internal--base_library.zip")
