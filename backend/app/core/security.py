"""JWT verification and role-based access control.

Token verification is deliberately ONE function, :func:`decode_token`. Whether
the token was minted by this application (AUTH_MODE=local) or by Supabase Auth
(AUTH_MODE=supabase), it is verified in the same place with the same code path.

That single function is the SSO-ready seam described in §13.10: swapping in a
government identity provider such as Parichay changes the issuer, the signing
key and the claims mapping here, and nothing else in the codebase. This is a
seam, not an integration — no government SSO is claimed or implemented.

It accepts both signing families, chosen by the token's own ``alg`` header:
symmetric HS256 against a shared secret, and asymmetric ES256/RS256 against a
public key fetched from the issuer's JWKS. Supabase moved user tokens to
per-project elliptic-curve keys, so a deployment can legitimately see either —
including both at once, while a key rotation is in flight.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
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

#: Supabase signs user tokens with a per-project elliptic-curve key and
#: publishes the public half as a JWKS. Projects created before that change
#: still sign HS256 with the shared ``SUPABASE_JWT_SECRET``, and local mode
#: always does, so both families have to be accepted — chosen by the token's
#: own ``alg`` header, never by configuration, because the two can differ
#: within one project during a key rotation.
ASYMMETRIC_ALGORITHMS = ("ES256", "ES384", "ES512", "RS256", "RS384", "RS512")

_JWKS_LOCK = threading.Lock()
_JWKS_CACHE: dict[str, Any] | None = None


def _fetch_jwks(*, force: bool = False) -> dict[str, Any]:
    """Return the project's JWKS, fetched once and then cached.

    Synchronous on purpose: verification happens inside a request and the
    result is cached for the life of the process, so this makes one blocking
    call on the first authenticated request rather than one per request.
    """
    global _JWKS_CACHE
    with _JWKS_LOCK:
        if _JWKS_CACHE is not None and not force:
            return _JWKS_CACHE
        if not settings.SUPABASE_URL:
            raise AuthError(
                "Token is signed with an asymmetric key, but SUPABASE_URL is "
                "not set, so its public key cannot be fetched."
            )
        url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthError(f"Could not fetch the token signing keys: {exc}") from exc
        _JWKS_CACHE = response.json()
        return _JWKS_CACHE


def _signing_key(kid: str | None) -> dict[str, Any]:
    """Find the public key for a key id, refetching once if it is unknown.

    An unrecognised ``kid`` normally means the project rotated its signing key
    since this process cached the set, so one forced refresh is tried before
    the token is rejected.
    """
    for attempt in (False, True):
        keys = _fetch_jwks(force=attempt).get("keys", [])
        for key in keys:
            if kid is None or key.get("kid") == kid:
                return key
    raise AuthError("Token was signed with a key this server does not recognise.")


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

    The key is chosen by the token's own ``alg`` header. An asymmetric token is
    verified against the project's published public key; a symmetric one against
    ``settings.jwt_secret``, which resolves to the Supabase JWT secret or the
    local secret depending on AUTH_MODE. Everything after the signature check is
    identical for both.
    """
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AuthError(f"Invalid or expired token: {exc}") from exc

    algorithm = str(header.get("alg") or JWT_ALGORITHM)
    key: Any
    if algorithm in ASYMMETRIC_ALGORITHMS:
        key = _signing_key(header.get("kid"))
    else:
        algorithm = JWT_ALGORITHM
        key = settings.jwt_secret
        if not key:
            raise AuthError(
                "Authentication is not configured on the server: no JWT secret is set."
            )

    try:
        claims: dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
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
        
    if profile.blocked_until and profile.blocked_until > datetime.now(timezone.utc):
        raise AuthError(f"Account is blocked until {profile.blocked_until.strftime('%Y-%m-%d %H:%M:%S UTC')}")

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
