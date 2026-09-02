"""Supabase auth backend — the locked-stack path.

Talks to Supabase Auth (GoTrue) over its REST interface with httpx. Registration
uses the admin endpoint with the service-role key, which lets the platform
create confirmed accounts for officials without an email round-trip. Login uses
the public password grant with the anon key.

Both keys stay server-side. The browser never sees the service-role key (§13.1).

Tokens minted here are verified by exactly the same ``core.security.decode_token``
used in local mode.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthError, ConflictError, NotConfiguredError
from app.core.logging import get_logger
from app.services.m1_identity.backend import AuthUserDTO, SessionDTO

log = get_logger(__name__)

_TIMEOUT = httpx.Timeout(15.0)


class SupabaseAuthBackend:
    """Identity against Supabase Auth."""

    name = "supabase"

    def __init__(self) -> None:
        if not settings.supabase_configured:
            raise NotConfiguredError(
                "AUTH_MODE=supabase requires SUPABASE_URL, SUPABASE_ANON_KEY, "
                "SUPABASE_SERVICE_ROLE_KEY and SUPABASE_JWT_SECRET to be set. "
                "Set AUTH_MODE=local to run without Supabase credentials."
            )
        self._base = settings.SUPABASE_URL.rstrip("/")

    async def register(
        self, *, session: AsyncSession, email: str, password: str
    ) -> AuthUserDTO:
        """Create a confirmed account through the GoTrue admin endpoint.

        ``session`` is unused: GoTrue is a remote service and cannot join the
        local transaction. The caller rolls back its own rows if this succeeds
        and the profile write then fails, leaving an unusable-but-harmless
        orphan identity that an administrator can clear.
        """
        del session  # documented above; kept for protocol conformance

        payload: dict[str, Any] = {
            "email": email.strip().lower(),
            "password": password,
            "email_confirm": True,
        }
        headers = {
            "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base}/auth/v1/admin/users", json=payload, headers=headers
            )

        if resp.status_code in (409, 422):
            raise ConflictError("An account with that email already exists.")
        if resp.status_code >= 400:
            log.error("supabase register failed: %s %s", resp.status_code, resp.text[:300])
            raise AuthError(f"Registration failed upstream ({resp.status_code}).")

        body = resp.json()
        user_id = body.get("id")
        if not user_id:
            raise AuthError("Supabase Auth returned no user id.")
        return AuthUserDTO(id=uuid.UUID(str(user_id)), email=body.get("email", email))

    async def login(
        self, *, session: AsyncSession, email: str, password: str
    ) -> SessionDTO:
        del session  # remote call; no local transaction involvement

        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base}/auth/v1/token",
                params={"grant_type": "password"},
                json={"email": email.strip().lower(), "password": password},
                headers=headers,
            )

        if resp.status_code >= 400:
            raise AuthError("Incorrect email or password.")

        body = resp.json()
        token = body.get("access_token")
        user = body.get("user") or {}
        user_id = user.get("id")
        if not token or not user_id:
            raise AuthError("Supabase Auth returned an unexpected session payload.")

        return SessionDTO(
            access_token=token,
            user_id=uuid.UUID(str(user_id)),
            email=user.get("email", email),
            expires_in=int(body.get("expires_in", 3600)),
        )
