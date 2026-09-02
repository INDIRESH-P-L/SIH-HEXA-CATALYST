"""The auth seam.

One protocol, two implementations. Which one runs is decided by AUTH_MODE and
nothing else in the application knows or cares which it is.

Note what is *not* here: token verification. That lives in
``core.security.decode_token`` and is shared by both backends, because both mint
HS256 tokens carrying the same claims. Registration and login are the only
operations that actually differ.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class AuthUserDTO:
    """A user as the auth backend sees them. No profile data."""

    id: uuid.UUID
    email: str


@dataclass(frozen=True)
class SessionDTO:
    """A minted session."""

    access_token: str
    user_id: uuid.UUID
    email: str
    expires_in: int


@runtime_checkable
class AuthBackend(Protocol):
    """Create and authenticate identities."""

    name: str

    async def register(
        self, *, session: AsyncSession, email: str, password: str
    ) -> AuthUserDTO:
        """Create an identity. Raises ConflictError if the email is taken.

        The local backend writes ``auth.users`` inside the caller's
        transaction, so registration is genuinely atomic with profile creation.
        The Supabase backend cannot be — GoTrue is a remote service — so it
        ignores the session and the caller compensates on failure.
        """
        ...

    async def login(
        self, *, session: AsyncSession, email: str, password: str
    ) -> SessionDTO:
        """Exchange credentials for an access token. Raises AuthError."""
        ...


def get_auth_backend() -> AuthBackend:
    """Resolve the configured auth backend.

    Imports are local so that choosing the local backend does not require
    Supabase settings to be present, and vice versa.
    """
    from app.core.config import settings

    if settings.AUTH_MODE == "supabase":
        from app.services.m1_identity.supabase_auth import SupabaseAuthBackend

        return SupabaseAuthBackend()

    from app.services.m1_identity.local_auth import LocalAuthBackend

    return LocalAuthBackend()
