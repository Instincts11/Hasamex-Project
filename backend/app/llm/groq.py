"""Dedicated Groq chat-completions client.

Architectural decision:
- API routes never call Groq. They go through LLMProvider → GroqLLMClient.
- Timeouts, retries, rate limits, and concurrency live here so business
  logic stays evidence-first and provider-agnostic.
- The model name comes from Settings, not from call sites.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.core.config import Settings, load_settings
from app.core.logging import log_pipeline
from app.core.secrets import redact_secrets
from app.llm.client import ChatMessage, LLMRawCompletion
from app.llm.errors import (
    LLMConfigError,
    LLMConnectionError,
    LLMError,
    LLMInvalidResponse,
    LLMPromptTooLarge,
    LLMTimeout,
    classify_http_status,
    groq_key_missing_message,
)
from app.llm.reliability import ConcurrencyLimiter, run_with_retries

GROQ_USER_AGENT = "Hasamex/0.1"


class GroqTransport(Protocol):
    def __call__(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: float,
    ) -> dict[str, Any]:
        ...


class GroqLLMClient:
    """Groq adapter that implements the existing LLMProvider protocol."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: GroqTransport | None = None,
        limiter: ConcurrencyLimiter | None = None,
        sleeper: Any | None = None,
    ) -> None:
        self._settings = settings or load_settings()
        if not self._settings.groq_api_key:
            raise LLMConfigError(groq_key_missing_message())
        self.model_name = self._settings.groq_model
        self._transport = transport or groq_http_post_json
        self._limiter = limiter or ConcurrencyLimiter(
            self._settings.groq_max_concurrent_requests
        )
        self._sleeper = sleeper

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        completion = self.complete(
            [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]
        )
        return completion.content

    def complete(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        self._assert_prompt_size(messages)
        with self._limiter:
            kwargs: dict[str, Any] = {
                "operation": lambda: self._once(messages),
                "max_attempts": self._settings.groq_max_retries + 1,
                "base_delay": self._settings.groq_retry_base_seconds,
            }
            if self._sleeper is not None:
                kwargs["sleeper"] = self._sleeper
            return run_with_retries(**kwargs)

    def _once(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        started = time.perf_counter()
        payload = {
            "model": self._settings.groq_model,
            "temperature": 0,
            "max_tokens": self._settings.groq_max_output_tokens,
            "response_format": {"type": "json_object"},
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": GROQ_USER_AGENT,
        }
        url = f"{self._settings.groq_base_url}/chat/completions"
        try:
            body = self._call_transport(url, headers, payload)
        except LLMError as exc:
            log_pipeline(
                "groq_request",
                provider="groq",
                model=self.model_name,
                status=exc.code,
            )
            raise
        latency_ms = (time.perf_counter() - started) * 1000
        content = _choice_content(body)
        usage = body.get("usage") or {}
        log_pipeline(
            "groq_request",
            provider="groq",
            model=str(body.get("model") or self.model_name),
            latency_ms=round(latency_ms, 2),
            status="success",
            retry_count=0,
        )
        return LLMRawCompletion(
            content=content,
            model=str(body.get("model") or self.model_name),
            latency_ms=latency_ms,
            prompt_tokens=_optional_int(usage.get("prompt_tokens")),
            completion_tokens=_optional_int(usage.get("completion_tokens")),
        )

    def _assert_prompt_size(self, messages: list[ChatMessage]) -> None:
        total = sum(len(item.content) for item in messages)
        if total > self._settings.groq_max_prompt_chars:
            raise LLMPromptTooLarge(
                f"Prompt exceeded {self._settings.groq_max_prompt_chars} characters."
            )

    def _call_transport(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        timeout = self._settings.groq_timeout_seconds
        try:
            return self._transport(url, headers, payload, timeout)
        except TypeError:
            return self._transport(url, headers, payload)  # type: ignore[call-arg, misc]


def groq_http_post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    request_headers = dict(headers)
    request_headers.setdefault("User-Agent", GROQ_USER_AGENT)
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except TimeoutError as exc:
        raise LLMTimeout("Groq request timed out.") from exc
    except socket.timeout as exc:
        raise LLMTimeout("Groq request timed out.") from exc
    except urllib.error.HTTPError as exc:
        detail = redact_secrets(exc.read().decode("utf-8", errors="replace"))
        retry_after = _parse_retry_after(exc.headers.get("Retry-After") if exc.headers else None)
        if exc.code == 403 and "1010" in detail:
            raise LLMConnectionError(
                "Groq request was blocked by the CDN. Retry with a User-Agent header."
            ) from exc
        error_cls = classify_http_status(exc.code)
        raise error_cls(
            f"Groq HTTP {exc.code}: {detail}",
            retry_after=retry_after,
        ) from exc
    except urllib.error.URLError as exc:
        reason = redact_secrets(str(exc.reason))
        if "timed out" in reason.lower():
            raise LLMTimeout("Groq request timed out.") from exc
        raise LLMConnectionError(f"Groq request failed: {reason}") from exc
    except OSError as exc:
        raise LLMConnectionError(f"Groq request failed: {exc}") from exc

    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMInvalidResponse("Groq response was not valid JSON.") from exc
    if not isinstance(body, dict):
        raise LLMInvalidResponse("Groq response JSON must be an object.")
    return body


def _choice_content(body: dict[str, Any]) -> str:
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMInvalidResponse("Groq response did not contain message content.") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMInvalidResponse("Groq response content was empty.")
    return content


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = float(value.strip())
    except ValueError:
        return None
    return parsed if parsed > 0 else None
