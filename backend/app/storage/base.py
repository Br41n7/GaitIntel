"""
Storage interface so "local filesystem for now, S3/Supabase later" is
a config change, not a rewrite. Every route/service should depend on
StorageBackend, never on `open()` or a hardcoded path directly.
"""
from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, file: BinaryIO) -> str:
        """Persist a file under `key`, return a path/URL that can be
        stored on the Assessment record and used to retrieve it later."""
        raise NotImplementedError

    @abstractmethod
    def get_path(self, key: str) -> str:
        """Return a filesystem path (or signed URL, for remote
        backends) usable to read the file back."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        raise NotImplementedError
