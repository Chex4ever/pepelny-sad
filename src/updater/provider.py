"""Update provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from src.updater.update_package import UpdatePackageInfo


class UpdateProvider(ABC):
    @abstractmethod
    def list_update_packages(self) -> list[UpdatePackageInfo]:
        ...

    @abstractmethod
    def download_bytes(self, url: str) -> bytes:
        ...
