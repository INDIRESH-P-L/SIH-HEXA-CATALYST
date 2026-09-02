"""JWT verification and role-based access control.

Token verification is deliberately ONE function, :func:`decode_token`. Whether
the token was minted by this application (AUTH_MODE=local) or by Supabase Auth
(AUTH_MODE=supabase), it is verified in the same place with the same code path.

That single function is the SSO-ready seam described in §13.10: swapping in a
government identity provider such as Parichay changes the issuer, the signing
key and the claims mapping here, and nothing else in the codebase. This is a
seam, not an integration — no government SSO is claimed or implemented.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import AuthError, ForbiddenError
from app.models.user import Profile, UserRole

#: auto_error=False so a missing header raises our own AuthError shape rather
#: than FastAPI's default, keeping every error response consistent.
_bearer = HTTPBearer(auto_error=False)

#: Supabase stamps this audience on user tokens; the local issuer matches it so
#: the verification path is identical in both modes.
JWT_AUDIENCE = "authenticated"
JWT_ALGORITHM = "HS256"


@dataclass(frozen=True)
class TokenClaims:
    """The subset of claims this application relies on."""

    sub: uuid.UUID
    email: str | None
    issuer: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class CurrentUser:
    """An authenticated caller, with roles read from the database."""

    id: uuid.UUID
    email: str | None
    roles: frozenset[str]
    profile: Profile

    def has_role(self, role: str) -> bool:
        return role in self.roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def is_trainer(self) -> bool:
        return "trainer" in self.roles


def create_access_token(
    *, user_id: uuid.UUID, email: str, extra: dict[str, Any] | None = None
) -> str:
    """Mint a local-mode access token.

    Only used when AUTH_MODE=local. Under AUTH_MODE=supabase, tokens are minted
    by GoTrue and this function is never called.
    """
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "aud": JWT_AUDIENCE,
        "iss": settings.LOCAL_JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.LOCAL_JWT_TTL_MIN)).timestamp()),
        "role": JWT_AUDIENCE,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.LOCAL_JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenClaims:
    """Verify a bearer token and return its claims.

    The signing secret comes from ``settings.jwt_secret``, which resolves to the
    Supabase JWT secret or the local secret depending on AUTH_MODE. Everything
    else about verification is identical between the two.
    """
    secret = settings.jwt_secret
    if not secret:
        raise AuthError(
            "Authentication is not configured on the server: no JWT secret is set."
        )
    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            options={"verify_aud": True},
        )
    except JWTError as exc:
        raise AuthError(f"Invalid or expired token: {exc}") from exc

    sub = claims.get("sub")
    if not sub:
        raise AuthError("Token carries no subject claim.")
    try:
        user_id = uuid.UUID(str(sub))
    except ValueError as exc:
        raise AuthError("Token subject is not a valid user id.") from exc

    return TokenClaims(
        sub=user_id,
        email=claims.get("email"),
        issuer=claims.get("iss"),
        raw=claims,
    )


async def load_roles(session: AsyncSession, user_id: uuid.UUID) -> frozenset[str]:
    """Read a user's roles from ``user_roles``.

    Roles are read server-side on every request. A role claim inside a token is
    never trusted, because a client controls what it sends (§13.3).
    """
    rows = await session.execute(select(UserRole.role).where(UserRole.user_id == user_id))
    return frozenset(rows.scalars().all())


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentUser:
    """FastAPI dependency: the authenticated caller, or 401."""
    if credentials is None or not credentials.credentials:
        raise AuthError("Missing bearer token.")

    claims = decode_token(credentials.credentials)

    profile = await session.get(Profile, claims.sub)
    if profile is None:
        raise AuthError("Authenticated user has no profile in this deployment.")

    roles = await load_roles(session, claims.sub)
    user = CurrentUser(
        id=claims.sub,
        email=claims.email,
        roles=roles or frozenset({"employee"}),
        profile=profile,
    )
    # Stashed so request-scoped helpers (activity logging) can reach it.
    request.state.current_user = user
    return user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_role(*allowed: str):
    """Build a dependency that admits only the listed roles.

    ``admin`` is always admitted, so an administrator can reach trainer screens
    without being separately granted the trainer role.
    """

    async def _dependency(user: CurrentUserDep) -> CurrentUser:
        if user.is_admin or any(user.has_role(r) for r in allowed):
            return user
        wanted = " or ".join(sorted(allowed))
        raise ForbiddenError(f"This action requires the {wanted} role.")

    return _dependency


require_trainer = require_role("trainer")
require_admin = require_role("admin")
