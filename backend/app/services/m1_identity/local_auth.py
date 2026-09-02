"""Local auth backend — the zero-credential path.

Writes the ``auth.users`` shim table created by ``000_local_auth_shim.sql`` and
mints its own HS256 tokens through ``core.security.create_access_token``.

Password hashing is PBKDF2-HMAC-SHA256 from the standard library: 200,000
iterations, a fresh 16-byte salt per user, stored in the widely used
``pbkdf2_sha256$iterations$salt$hash`` form. That is a deliberate choice to
avoid adding a dependency outside the locked stack for a path that never runs
in the Supabase deployment. It is adequate for a prototype; a production
deployment uses Supabase Auth or a government identity provider, neither of
which stores passwords here at all.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthError, ConflictError
from app.core.security import create_access_token
from app.models.user import AuthUser
from app.services.m1_identity.backend import AuthUserDTO, SessionDTO

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """Return a self-describing password hash string."""
    if salt is None:
        salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return "{}${}${}${}".format(
        _ALGORITHM,
        _ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time verification against a stored hash."""
    try:
        algorithm, iterations, salt_b64, hash_b64 = encoded.split("$", 3)
        if algorithm != _ALGORITHM:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


class LocalAuthBackend:
    """Identity against the local ``auth.users`` table."""

    name = "local"

    async def register(
        self, *, session: AsyncSession, email: str, password: str
    ) -> AuthUserDTO:
        normalised = email.strip().lower()
        existing = await session.scalar(
            select(AuthUser).where(AuthUser.email == normalised)
        )
        if existing is not None:
            raise ConflictError("An account with that email already exists.")

        user = AuthUser(
            id=uuid.uuid4(),
            email=normalised,
            encrypted_password=hash_password(password),
        )
        session.add(user)
        # Flush, not commit: registration must stay atomic with the profile and
        # role rows the caller creates in the same transaction.
        await session.flush()
        return AuthUserDTO(id=user.id, email=user.email)

    async def login(
        self, *, session: AsyncSession, email: str, password: str
    ) -> SessionDTO:
        normalised = email.strip().lower()
        user = await session.scalar(select(AuthUser).where(AuthUser.email == normalised))
        if user is None or not verify_password(password, user.encrypted_password):
            # One message for both cases, so the endpoint does not reveal
            # whether an address is registered.
            raise AuthError("Incorrect email or password.")

        token = create_access_token(user_id=user.id, email=user.email)
        return SessionDTO(
            access_token=token,
            user_id=user.id,
            email=user.email,
            expires_in=settings.LOCAL_JWT_TTL_MIN * 60,
        )
