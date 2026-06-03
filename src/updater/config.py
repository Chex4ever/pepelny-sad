"""Updater configuration (GitHub Releases now, CDN later via env)."""
from __future__ import annotations

import os

DEFAULT_REPO = "Chex4ever/pepelny-sad"
DEFAULT_PROVIDER = "github"


def update_repo() -> str:
    return os.environ.get("PEPELNY_UPDATE_REPO", DEFAULT_REPO)


def update_provider_name() -> str:
    return os.environ.get("PEPELNY_UPDATE_PROVIDER", DEFAULT_PROVIDER)


def update_base_url() -> str | None:
    """Optional CDN base URL override for future HttpCdnProvider."""
    return os.environ.get("PEPELNY_UPDATE_BASE_URL")
