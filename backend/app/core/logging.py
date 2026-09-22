"""Structured pipeline logging.

Architectural decision:
- Log IDs, scores, model, and validation outcome so a bad citation can be
  debugged without treating lexical score as model confidence.
- Never log API keys, bearer tokens, or raw secrets.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.secrets import redact_secrets, sanitize_value

logger = logging.getLogger("hasamex")


class _SecretRedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_value(record.args)
            else:
                record.args = tuple(sanitize_value(item) for item in record.args)
        return True


def log_pipeline(event: str, **fields: Any) -> None:
    payload = sanitize_value({"event": event, **fields})
    logger.info(json.dumps(payload, default=str, sort_keys=True))


def log_trace(trace: Any) -> None:
    """Log the full pipeline trace. Scores are ranks, not model confidence."""
    payload = trace.model_dump() if hasattr(trace, "model_dump") else dict(trace)
    payload["event"] = "pipeline"
    logger.info(json.dumps(sanitize_value(payload), default=str, sort_keys=True))


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level.upper(), format="%(message)s", force=False)
    if not any(isinstance(item, _SecretRedactFilter) for item in logger.filters):
        logger.addFilter(_SecretRedactFilter())
    root = logging.getLogger()
    if not any(isinstance(item, _SecretRedactFilter) for item in root.filters):
        root.addFilter(_SecretRedactFilter())
