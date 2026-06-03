"""Tests for update package chain planning."""
from src.updater.update_package import (
    UpdatePackageInfo,
    parse_update_package_filename,
    plan_update_chain,
    update_package_filename,
)


def _pkg(to_version: str, applies_from: tuple[str, ...]) -> UpdatePackageInfo:
    return UpdatePackageInfo(
        to_version=to_version,
        platform_id="win-x64",
        applies_from=applies_from,
        download_url=f"https://example.test/{to_version}.zip",
        release_tag=f"v{to_version}",
    )


def test_update_package_filename():
    assert update_package_filename("0.2.12", "win-x64") == "pepelny-sad-update-0-2-12-win-x64.zip"


def test_parse_update_package_filename():
    name = "pepelny-sad-update-0-2-12-win-x64.zip"
    assert parse_update_package_filename(name, "win-x64") == "0.2.12"
    assert parse_update_package_filename(name, "linux-x64") is None


def test_plan_update_chain_steps_forward():
    packages = [
        _pkg("0.2.10", ("0.2.9",)),
        _pkg("0.2.12", ("0.2.11",)),
        _pkg("0.2.11", ("0.2.10",)),
        _pkg("0.2.9", ("0.2.8",)),
    ]
    chain = plan_update_chain("0.2.8", packages)
    assert [p.to_version for p in chain] == ["0.2.9", "0.2.10", "0.2.11", "0.2.12"]


def test_plan_update_chain_picks_nearest_when_not_on_latest():
    packages = [
        _pkg("0.2.12", ("0.2.11",)),
        _pkg("0.2.11", ("0.2.10",)),
    ]
    chain = plan_update_chain("0.2.10", packages)
    assert [p.to_version for p in chain] == ["0.2.11", "0.2.12"]


def test_plan_update_chain_empty_when_up_to_date():
    packages = [_pkg("0.2.12", ("0.2.11",))]
    assert plan_update_chain("0.2.12", packages) == []
