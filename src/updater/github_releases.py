"""Fetch updates from GitHub Releases."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from src.updater.provider import UpdateProvider


class GitHubReleasesProvider(UpdateProvider):
    def __init__(self, repo: str, platform_id: str):
        self.repo = repo
        self.platform_id = platform_id

    def _api_url(self) -> str:
        return f"https://api.github.com/repos/{self.repo}/releases/latest"

    def fetch_manifest(self) -> dict[str, Any]:
        req = urllib.request.Request(
            self._api_url(),
            headers={"Accept": "application/vnd.github+json", "User-Agent": "pepelny-sad-updater"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            release = json.loads(resp.read().decode("utf-8"))
        manifest_name = f"manifest-{self.platform_id}.json"
        for asset in release.get("assets", []):
            if asset.get("name") == manifest_name:
                with urllib.request.urlopen(asset["browser_download_url"], timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
        raise FileNotFoundError(f"Release asset not found: {manifest_name}")

    def download_file(self, url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "pepelny-sad-updater"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        destination.write_bytes(data)
