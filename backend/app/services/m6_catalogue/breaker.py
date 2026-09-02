"""A small circuit breaker for the catalogue call path.

Deliberately about thirty lines and in-memory. There is no Redis and no
distributed state here, because the application is a single process (§1 rule 4).

Its job in the demo: with MOCK_FLAKY=true the mock service returns 503 on a
small fraction of requests. After a few consecutive failures the breaker opens,
catalogue reads fall back to the local ``courses`` mirror, and the interface
keeps working instead of showing an error. It closes again after a cooldown.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class CircuitBreaker:
    """Closed → (threshold failures) → Open → (cooldown) → Half-open → Closed."""

    name: str
    threshold: int = 3
    cooldown_s: float = 30.0
    _failures: int = field(default=0, init=False)
    _opened_at: float | None = field(default=None, init=False)

    @property
    def is_open(self) -> bool:
        """True while calls should be skipped entirely."""
        if self._opened_at is None:
            return False
        if (time.monotonic() - self._opened_at) >= self.cooldown_s:
            # Cooldown elapsed: allow one trial call through (half-open).
            log.info("circuit %s: cooldown elapsed, half-open", self.name)
            self._opened_at = None
            self._failures = self.threshold - 1
            return False
        return True

    def record_success(self) -> None:
        if self._failures or self._opened_at:
            log.info("circuit %s: closed after success", self.name)
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.threshold and self._opened_at is None:
            self._opened_at = time.monotonic()
            log.warning(
                "circuit %s: OPEN after %d consecutive failures; "
                "serving from the local catalogue mirror for %.0fs",
                self.name,
                self._failures,
                self.cooldown_s,
            )

    def reset(self) -> None:
        self._failures = 0
        self._opened_at = None

    @property
    def state(self) -> str:
        return "open" if self.is_open else ("degraded" if self._failures else "closed")
