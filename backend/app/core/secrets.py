"""Redact secrets before they can reach logs or HTTP error bodies."""

from __future__ import annotations

import re
from typing import Any

_SECRET_RE = re.compile(
    r"(gsk_[A-Za-z0-9]+)"
    r"|(sk-[A-Za-z0-9]+)"
    r"|(Bearer\s+\S+)"
    r"|((?:GROQ_API_KEY|OPENAI_API_KEY|HASAMEX_LLM_API_KEY)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


def redact_secrets(value: str) -> str:
    return _SECRET_RE.sub("[redacted]", value)


def contains_secret(value: str) -> bool:
    return _SECRET_RE.search(value) is not None


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, dict):
        return {str(key): sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value
