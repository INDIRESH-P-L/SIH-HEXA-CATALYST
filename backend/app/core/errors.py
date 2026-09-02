"""Domain exceptions and their HTTP mapping.

Keeping these in one place means every service can raise a meaningful error
without importing FastAPI, which keeps the pure-function modules (M4 especially)
free of framework imports.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for every error this application raises deliberately."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, detail: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationFailedError(AppError):
    status_code = 422
    code = "validation_failed"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class LLMUnavailable(AppError):
    """Raised by ai.llm_client when Groq cannot serve a request.

    Every caller catches this and substitutes a deterministic, non-AI fallback
    (§1 rule 7). It is never allowed to reach the client as a 5xx.
    """

    status_code = 503
    code = "llm_unavailable"


class PIILeakError(AppError):
    """Raised by ai.scrub when a payload bound for the LLM contains personal data.

    This is a hard stop, not a warning. Nothing leaves the process (§13.5).
    """

    status_code = 500
    code = "pii_leak_blocked"


class NotConfiguredError(AppError):
    """A seam exists but its production implementation has no credentials."""

    status_code = 501
    code = "not_configured"


class UpstreamUnavailable(AppError):
    """The catalogue service could not be reached."""

    status_code = 502
    code = "upstream_unavailable"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "detail": exc.detail},
        )
