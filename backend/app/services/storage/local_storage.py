"""Local-disk storage. The zero-credential path."""

from __future__ import annotations

import uuid
from pathlib import Path

import anyio

from app.core.config import settings
from app.core.errors import NotFoundError
from app.services.storage.provider import StoredObject, build_key


class LocalStorage:
    """Stores objects under ``backend/storage/`` using the shared key layout."""

    name = "local"

    def __init__(self) -> None:
        self.root: Path = settings.storage_root
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        """Resolve a key to a path, refusing anything that escapes the root."""
        candidate = (self.root / path).resolve()
        if not candidate.is_relative_to(self.root.resolve()):
            raise NotFoundError("Invalid storage path.")
        return candidate

    async def put(
        self, *, user_id: uuid.UUID, data: bytes, extension: str, content_type: str
    ) -> StoredObject:
        key = build_key(user_id, extension)
        target = self._resolve(key)
        await anyio.to_thread.run_sync(lambda: target.parent.mkdir(parents=True, exist_ok=True))
        await anyio.to_thread.run_sync(lambda: target.write_bytes(data))
        return StoredObject(path=key, size_bytes=len(data), content_type=content_type)

    async def get(self, path: str) -> bytes:
        target = self._resolve(path)
        if not target.is_file():
            raise NotFoundError(f"Stored object not found: {path}")
        return await anyio.to_thread.run_sync(target.read_bytes)

    async def delete(self, path: str) -> None:
        target = self._resolve(path)
        if target.is_file():
            await anyio.to_thread.run_sync(target.unlink)
