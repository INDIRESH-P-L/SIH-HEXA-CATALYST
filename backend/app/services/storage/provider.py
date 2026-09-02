"""Storage seam.

Uploaded learning material goes to Supabase Storage in the locked-stack
deployment and to local disk otherwise. Both use the same key layout,
``materials/{user_id}/{uuid}.{ext}``, so switching STORAGE_MODE does not
invalidate the ``storage_path`` values already in the database.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class StoredObject:
    """Where an uploaded file ended up."""

    path: str
    size_bytes: int
    content_type: str


@runtime_checkable
class StorageProvider(Protocol):
    name: str

    async def put(
        self, *, user_id: uuid.UUID, data: bytes, extension: str, content_type: str
    ) -> StoredObject:
        """Store bytes under a server-generated key and return its location."""
        ...

    async def get(self, path: str) -> bytes:
        """Read an object back."""
        ...

    async def delete(self, path: str) -> None:
        """Remove an object. Missing objects are not an error."""
        ...


def build_key(user_id: uuid.UUID, extension: str) -> str:
    """Server-generated object key.

    The client filename is never used to build this. It is kept in
    ``learning_materials.filename`` for display only (§13.7).
    """
    ext = extension.lower().lstrip(".")
    return f"materials/{user_id}/{uuid.uuid4()}.{ext}"


def get_storage_provider() -> StorageProvider:
    from app.core.config import settings

    if settings.STORAGE_MODE == "supabase":
        from app.services.storage.supabase_storage import SupabaseStorage

        return SupabaseStorage()

    from app.services.storage.local_storage import LocalStorage

    return LocalStorage()
