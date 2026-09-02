"""Embeddings — FastEmbed, in-process, on CPU.

Groq has NO embeddings endpoint. It serves chat models and Whisper only.
``groq.embeddings.create()`` does not exist and must never be written.

FastEmbed runs BAAI/bge-small-en-v1.5 (384 dimensions) through ONNX Runtime:
no torch, no GPU, no API key, no rate limit and no network call once the model
is on disk. The model is loaded once and reused; it is safe for concurrent
reads. ``warm()`` is called from the FastAPI lifespan so the first real request
does not pay the load cost.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - import cost avoided at runtime
    from fastembed import TextEmbedding

log = get_logger(__name__)

_model: "TextEmbedding | None" = None
_lock = threading.Lock()


def get_model() -> "TextEmbedding":
    """Return the process-wide embedding model, loading it on first use."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:  # re-check inside the lock
                from fastembed import TextEmbedding

                log.info("loading embedding model %s", settings.EMBED_MODEL)
                _model = TextEmbedding(model_name=settings.EMBED_MODEL)
                log.info("embedding model ready (%d dims)", settings.EMBED_DIM)
    return _model


def embed_one(text: str) -> list[float]:
    """Embed a single string. Returns a 384-float list."""
    return list(get_model().embed([text]))[0].tolist()


def embed_many(texts: list[str]) -> list[list[float]]:
    """Embed a batch. Order of the output matches the order of the input."""
    if not texts:
        return []
    return [v.tolist() for v in get_model().embed(texts)]


def to_pgvector(vec: list[float]) -> str:
    """Render a vector in the literal form pgvector accepts.

    Binding the vector as text and casting it in SQL (``:emb::vector(384)``)
    avoids having to register an asyncpg codec, which is awkward under
    SQLAlchemy's async engine.
    """
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors.

    Used by the near-duplicate check in the M8 validation gate when comparing
    items inside a single generated batch, where nothing has been written to
    the database yet.
    """
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def warm() -> bool:
    """Load the model and run one tiny embedding. Returns success."""
    try:
        vec = embed_one("warm up")
        if len(vec) != settings.EMBED_DIM:
            log.error(
                "embedding dim mismatch: model gave %d, EMBED_DIM=%d",
                len(vec),
                settings.EMBED_DIM,
            )
            return False
        return True
    except Exception as exc:  # pragma: no cover - environment dependent
        log.error("embedding warm-up failed: %s", exc)
        return False


def is_ready() -> bool:
    return _model is not None
