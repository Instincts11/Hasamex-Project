"""Timeouts, bounded retries, backoff, and concurrency for Groq calls."""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from typing import TypeVar

from app.core.logging import log_pipeline
from app.llm.errors import LLMError, LLMRateLimited

T = TypeVar("T")


class ConcurrencyLimiter:
    """Process-local cap on simultaneous Groq requests."""

    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("GROQ_MAX_CONCURRENT_REQUESTS must be at least 1.")
        self.limit = limit
        self._semaphore = threading.BoundedSemaphore(limit)
        self._active = 0
        self._lock = threading.Lock()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    def acquire(self, timeout: float) -> bool:
        return self._semaphore.acquire(timeout=timeout)

    def release(self) -> None:
        self._semaphore.release()

    def __enter__(self) -> ConcurrencyLimiter:
        if not self.acquire(timeout=60.0):
            raise LLMRateLimited("Concurrency limit reached for Groq requests.")
        with self._lock:
            self._active += 1
        return self

    def __exit__(self, *exc: object) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)
        self.release()


def backoff_seconds(
    attempt: int,
    *,
    base: float = 0.4,
    cap: float = 8.0,
    retry_after: float | None = None,
    jitter: bool = True,
) -> float:
    if retry_after is not None and retry_after > 0:
        delay = min(float(retry_after), cap)
    else:
        delay = min(cap, base * (2**attempt))
    if jitter:
        delay *= 0.5 + random.random()
    return delay


def run_with_retries(
    operation: Callable[[], T],
    *,
    max_attempts: int,
    base_delay: float = 0.4,
    cap: float = 8.0,
    sleeper: Callable[[float], None] = time.sleep,
    log_event: str = "groq_retry",
) -> T:
    """Retry only transient provider failures. Never loop forever."""

    attempts = max(1, max_attempts)
    last_error: LLMError | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except LLMError as exc:
            last_error = exc
            remaining = attempts - attempt - 1
            if remaining <= 0 or not exc.retryable:
                raise
            delay = backoff_seconds(
                attempt,
                base=base_delay,
                cap=cap,
                retry_after=exc.retry_after,
            )
            log_pipeline(
                log_event,
                provider="groq",
                attempt=attempt + 1,
                max_attempts=attempts,
                status=exc.code,
                backoff_seconds=round(delay, 3),
            )
            sleeper(delay)
    assert last_error is not None
    raise last_error
