"""In-flight duplicate protection for analysis requests."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

from app.llm.errors import LLMDuplicateRequest

T = TypeVar("T")


class ExclusiveRequestGate:
    """Reject a second identical request while the first is still running."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: set[str] = set()

    def acquire(self, key: str) -> bool:
        with self._lock:
            if key in self._active:
                return False
            self._active.add(key)
            return True

    def release(self, key: str) -> None:
        with self._lock:
            self._active.discard(key)

    def run(self, key: str, operation: Callable[[], T]) -> T:
        if not self.acquire(key):
            raise LLMDuplicateRequest(
                "Duplicate analysis request is already in progress.",
                user_message="This analysis request is already in progress.",
            )
        try:
            return operation()
        finally:
            self.release(key)
