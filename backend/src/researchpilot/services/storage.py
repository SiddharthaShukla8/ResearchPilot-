"""Storage interface and local filesystem adapter for uploaded PDFs."""
import os
from abc import ABC, abstractmethod
from pathlib import Path

from researchpilot.core.config import get_settings


class StorageBackend(ABC):
    """Abstract interface for storing and retrieving private uploaded documents."""

    @abstractmethod
    async def save(self, storage_key: str, data: bytes) -> str:
        """Persist file bytes under storage_key and return canonical path/URI."""

    @abstractmethod
    async def read(self, storage_key: str) -> bytes:
        """Read and return file bytes for storage_key."""

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Delete file associated with storage_key."""

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check if file exists."""


class LocalFileStorage(StorageBackend):
    """Local filesystem implementation of private document storage."""

    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            settings = get_settings()
            self.base_dir = settings.local_storage_path
        else:
            self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, storage_key: str) -> Path:
        # Prevent directory traversal attacks
        safe_key = os.path.basename(storage_key)
        return self.base_dir / safe_key

    async def save(self, storage_key: str, data: bytes) -> str:
        target_path = self._get_path(storage_key)
        with open(target_path, "wb") as f:
            f.write(data)
        return str(target_path)

    async def read(self, storage_key: str) -> bytes:
        target_path = self._get_path(storage_key)
        if not target_path.exists():
            raise FileNotFoundError(f"Storage key {storage_key} does not exist")
        with open(target_path, "rb") as f:
            return f.read()

    async def delete(self, storage_key: str) -> bool:
        target_path = self._get_path(storage_key)
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    def exists(self, storage_key: str) -> bool:
        return self._get_path(storage_key).exists()
