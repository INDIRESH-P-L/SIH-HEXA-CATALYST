"""Application configuration.

Every runtime choice lives here and is read from the environment. There are no
absolute URLs anywhere else in the codebase (§13.9).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR: Path = Path(__file__).resolve().parents[2]

AuthMode = Literal["local", "supabase"]
StorageMode = Literal["local", "supabase"]
CatalogueProviderName = Literal["mock", "igot"]


class Settings(BaseSettings):
    """Typed settings. Instantiated once via :func:`get_settings`."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── app ──────────────────────────────────────────────────────────────────
    APP_ENV: str = "dev"
    APP_NAME: str = "AI-Enabled Skill Intelligence Platform"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ── data seam ────────────────────────────────────────────────────────────
    #
    # There is no local-PostgreSQL default. The platform runs against Supabase,
    # and a default pointing at localhost is worse than none: on a machine that
    # happens to run Postgres it connects to the wrong database and reports
    # success. ``.invalid`` is reserved by RFC 2606 and can never resolve, so an
    # unset DB_URL fails immediately and says why, while still letting the unit
    # tests import the app without a .env on a fresh clone.
    DB_URL: str = "postgresql+asyncpg://unset:unset@db-url-not-configured.invalid:5432/unset"
    DB_ECHO: bool = False

    # ── auth seam ────────────────────────────────────────────────────────────
    AUTH_MODE: AuthMode = "local"
    LOCAL_JWT_SECRET: str = "dev-only-insecure-secret-change-me"
    LOCAL_JWT_ISSUER: str = "sip-local"
    LOCAL_JWT_TTL_MIN: int = 720

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # ── storage seam ─────────────────────────────────────────────────────────
    STORAGE_MODE: StorageMode = "local"
    LOCAL_STORAGE_DIR: str = "./storage"
    SUPABASE_STORAGE_BUCKET: str = "materials"
    MAX_UPLOAD_MB: int = 10

    # ── catalogue seam ───────────────────────────────────────────────────────
    CATALOGUE_PROVIDER: CatalogueProviderName = "mock"
    MOCK_CATALOGUE_URL: str = "http://localhost:8001"
    MOCK_API_KEY: str = "sih-2026-mock-key"
    CATALOGUE_TIMEOUT_S: float = 10.0
    CATALOGUE_BREAKER_THRESHOLD: int = 3
    CATALOGUE_BREAKER_COOLDOWN_S: float = 30.0

    # ── llm ──────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    LLM_ENABLED: bool = True
    LLM_TIMEOUT_S: float = 30.0
    LLM_CACHE_ENABLED: bool = True
    # Groq retired the Llama 3.x hosted models. The GPT-OSS family replaces
    # them: 120b writes the prose, 20b generates MCQs because it is one of the
    # models that honours strict ``json_schema`` (see ai/schemas_json.py), and
    # 20b doubles as the rate-limit fallback.
    MODEL_MCQ: str = "openai/gpt-oss-20b"
    MODEL_TEXT: str = "openai/gpt-oss-120b"
    MODEL_FALLBACK: str = "openai/gpt-oss-20b"

    # ── embeddings ───────────────────────────────────────────────────────────
    EMBED_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBED_DIM: int = 384

    # ── stretch scope ────────────────────────────────────────────────────────
    ASSISTANT_ENABLED: bool = False

    # ── keep-alive (Supabase free projects pause after 7 idle days) ──────────
    KEEPALIVE_ENABLED: bool = False
    KEEPALIVE_INTERVAL_H: int = 6

    MAX_UPLOAD_BYTES: int = Field(default=0, exclude=True)

    @field_validator("MAX_UPLOAD_BYTES", mode="before")
    @classmethod
    def _ignore_supplied(cls, _v: object) -> int:
        return 0

    # ── derived ──────────────────────────────────────────────────────────────
    @property
    def cors_origin_list(self) -> list[str]:
        """Explicit allowlist. Never ``*`` (§13.8)."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def upload_limit_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def storage_root(self) -> Path:
        p = Path(self.LOCAL_STORAGE_DIR)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()

    @property
    def db_port(self) -> int | None:
        """Port of the configured database URL, if any."""
        try:
            return urlsplit(self.DB_URL).port
        except ValueError:
            return None

    @property
    def is_transaction_pooler(self) -> bool:
        """Supavisor transaction mode listens on 6543.

        In that mode asyncpg must disable its prepared-statement cache and
        SQLAlchemy must not pool, or you get intermittent
        ``DuplicatePreparedStatementError`` (§3 critical fact 5).
        """
        return self.db_port == 6543

    @property
    def jwt_secret(self) -> str:
        """The one secret used to verify bearer tokens, whichever seam is active."""
        return (
            self.SUPABASE_JWT_SECRET
            if self.AUTH_MODE == "supabase"
            else self.LOCAL_JWT_SECRET
        )

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_ENABLED and self.GROQ_API_KEY.strip())

    @property
    def supabase_configured(self) -> bool:
        return bool(
            self.SUPABASE_URL.strip()
            and self.SUPABASE_ANON_KEY.strip()
            and self.SUPABASE_SERVICE_ROLE_KEY.strip()
            and self.SUPABASE_JWT_SECRET.strip()
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
