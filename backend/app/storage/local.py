import os
import shutil
from typing import BinaryIO

from app.core.config import settings
from app.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str | None = None):
        self.base_path = base_path or settings.video_storage_path
        os.makedirs(self.base_path, exist_ok=True)

    def _full_path(self, key: str) -> str:
        return os.path.join(self.base_path, key)

    def save(self, key: str, file: BinaryIO) -> str:
        full_path = self._full_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file, f)
        return full_path

    def get_path(self, key: str) -> str:
        return self._full_path(key)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))


def get_storage_backend() -> StorageBackend:
    # Single switch point for later swapping to S3/Supabase Storage.
    return LocalStorage()
