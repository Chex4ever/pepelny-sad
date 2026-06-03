"""Update provider abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class UpdateProvider(ABC):
    @abstractmethod
    def fetch_manifest(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def download_file(self, url: str, destination: Path) -> None:
        ...
