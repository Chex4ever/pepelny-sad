"""Fetch update packages from GitHub Releases."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from src.updater.provider import UpdateProvider
from src.updater.update_package import UpdatePackageInfo, parse_update_package_filename, previous_patch_version


class GitHubReleasesProvider(UpdateProvider):
    def __init__(self, repo: str, platform_id: str):
        self.repo = repo
        self.platform_id = platform_id

    def _releases_url(self, page: int = 1) -> str:
        return f"https://api.github.com/repos/{self.repo}/releases?per_page=100&page={page}"

    def _request_json(self, url: str) -> Any:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "pepelny-sad-updater"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def list_update_packages(self) -> list[UpdatePackageInfo]:
        packages: list[UpdatePackageInfo] = []
        page = 1
        while True:
            releases = self._request_json(self._releases_url(page))
            if not releases:
                break
            for release in releases:
                tag = release.get("tag_name", "")
                for asset in release.get("assets", []):
                    name = asset.get("name", "")
                    to_version = parse_update_package_filename(name, self.platform_id)
                    if not to_version:
                        continue
                    try:
                        applies = (previous_patch_version(to_version),)
                    except ValueError:
                        applies = ()
                    packages.append(
                        UpdatePackageInfo(
                            to_version=to_version,
                            platform_id=self.platform_id,
                            applies_from=applies,
                            download_url=asset["browser_download_url"],
                            release_tag=tag,
                        )
                    )
            if len(releases) < 100:
                break
            page += 1
        return packages

    def download_bytes(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "pepelny-sad-updater"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.read()
