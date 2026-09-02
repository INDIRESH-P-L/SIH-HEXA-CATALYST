"""Supabase Storage backend — the locked-stack path."""

from __future__ import annotations

import uuid

import httpx

from app.core.config import settings
from app.core.errors import NotConfiguredError, NotFoundError, UpstreamUnavailable
from app.services.storage.provider import StoredObject, build_key

_TIMEOUT = httpx.Timeout(30.0)


class SupabaseStorage:
    """Objects in the configured Supabase Storage bucket.

    Uses the service-role key, which stays server-side. The bucket is private;
    the backend streams file contents to authorised callers rather than handing
    out public URLs.
    """

    name = "supabase"

    def __init__(self) -> None:
        if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
            raise NotConfiguredError(
                "STORAGE_MODE=supabase requires SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY. Set STORAGE_MODE=local to use disk."
            )
        self._base = settings.SUPABASE_URL.rstrip("/")
        self._bucket = settings.SUPABASE_STORAGE_BUCKET

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        }

    async def put(
        self, *, user_id: uuid.UUID, data: bytes, extension: str, content_type: str
    ) -> StoredObject:
        key = build_key(user_id, extension)
        url = f"{self._base}/storage/v1/object/{self._bucket}/{key}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                content=data,
                headers={**self._headers, "Content-Type": content_type},
            )
        if resp.status_code >= 400:
            raise UpstreamUnavailable(
                f"Supabase Storage upload failed ({resp.status_code})."
            )
        return StoredObject(path=key, size_bytes=len(data), content_type=content_type)

    async def get(self, path: str) -> bytes:
        url = f"{self._base}/storage/v1/object/{self._bucket}/{path}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=self._headers)
        if resp.status_code == 404:
            raise NotFoundError(f"Stored object not found: {path}")
        if resp.status_code >= 400:
            raise UpstreamUnavailable(
                f"Supabase Storage read failed ({resp.status_code})."
            )
        return resp.content

    async def delete(self, path: str) -> None:
        url = f"{self._base}/storage/v1/object/{self._bucket}/{path}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.delete(url, headers=self._headers)
        if resp.status_code >= 400 and resp.status_code != 404:
            raise UpstreamUnavailable(
                f"Supabase Storage delete failed ({resp.status_code})."
            )
