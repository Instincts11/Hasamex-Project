"""LLM provider abstraction.

Architectural decision:
- Callers depend on LLMProvider, not Groq or OpenAI. Tests use
  MockLLMProvider and never need a key or network.
- The provider returns raw text plus usage metadata. Parsing, schema
  checks, and quote resolution stay in deterministic code.
- Hosted adapters take an injectable transport so a live HTTP call
  is not required to unit-test request shaping.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from app.core.config import ConfigError, Settings, load_settings
from app.llm.errors import LLMConfigError, LLMError

HttpTransport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str


class LLMRawCompletion(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMProvider(Protocol):
    model_name: str

    def complete(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        ...


class LLMClient(Protocol):
    """Narrow generate() surface from the reliability spec."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...


class MockLLMProvider:
    """Scripted provider for tests. Responses are consumed in order."""

    def __init__(self, responses: list[str | dict[str, Any]] | None = None) -> None:
        self.model_name = "mock"
        self.calls: list[list[ChatMessage]] = []
        self._responses: list[str | dict[str, Any]] = list(responses or [])

    def queue(self, response: str | dict[str, Any]) -> None:
        self._responses.append(response)

    def complete(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        self.calls.append(messages)
        if not self._responses:
            raise LLMError("MockLLMProvider has no queued responses.")
        item = self._responses.pop(0)
        content = item if isinstance(item, str) else json.dumps(item)
        return LLMRawCompletion(
            content=content,
            model=self.model_name,
            latency_ms=0.0,
            prompt_tokens=0,
            completion_tokens=0,
        )


class OpenAIProvider:
    """OpenAI Chat Completions adapter. Key comes from Settings, not source."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: HttpTransport | None = None,
    ) -> None:
        self._settings = settings or load_settings()
        if not self._settings.llm_api_key:
            raise LLMConfigError(
                "OPENAI_API_KEY or HASAMEX_LLM_API_KEY is required for the openai provider."
            )
        self.model_name = self._settings.llm_model
        self._transport = transport or _http_post_json

    def complete(self, messages: list[ChatMessage]) -> LLMRawCompletion:
        started = time.perf_counter()
        payload = {
            "model": self._settings.llm_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": item.role, "content": item.content} for item in messages],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._settings.llm_base_url}/chat/completions"
        body = self._transport(url, headers, payload)
        latency_ms = (time.perf_counter() - started) * 1000
        content = _choice_content(body)
        usage = body.get("usage") or {}
        return LLMRawCompletion(
            content=content,
            model=str(body.get("model") or self.model_name),
            latency_ms=latency_ms,
            prompt_tokens=_optional_int(usage.get("prompt_tokens")),
            completion_tokens=_optional_int(usage.get("completion_tokens")),
        )


def create_provider(
    settings: Settings | None = None,
    transport: HttpTransport | None = None,
) -> LLMProvider:
    try:
        resolved = settings or load_settings()
    except ConfigError as exc:
        raise LLMConfigError(str(exc)) from exc
    if resolved.llm_provider == "mock":
        return MockLLMProvider()
    if resolved.llm_provider == "openai":
        return OpenAIProvider(resolved, transport=transport)
    if resolved.llm_provider == "groq":
        from app.llm.groq import GroqLLMClient

        return GroqLLMClient(resolved, transport=transport)
    raise LLMConfigError(f"Unknown HASAMEX_LLM_PROVIDER: {resolved.llm_provider}")


def _choice_content(body: dict[str, Any]) -> str:
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("OpenAI response did not contain message content.") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMError("OpenAI response content was empty.")
    return content


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _http_post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float = 30.0,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMError(f"LLM HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"LLM request failed: {exc.reason}") from exc
