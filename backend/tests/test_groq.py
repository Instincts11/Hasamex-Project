from __future__ import annotations

import logging
import os
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.api.state import build_context
from app.core.config import ConfigError, Settings, load_settings
from app.core.dedup import ExclusiveRequestGate
from app.core.logging import configure_logging, log_pipeline
from app.core.secrets import redact_secrets
from app.llm.client import ChatMessage, create_provider
from app.llm.errors import (
    LLM_AUTHENTICATION_ERROR,
    LLM_PROVIDER_UNAVAILABLE,
    LLMAuthenticationError,
    LLMConfigError,
    LLMDuplicateRequest,
    LLMInvalidResponse,
    LLMPromptTooLarge,
    LLMProviderUnavailable,
    LLMRateLimited,
    LLMTimeout,
)
from app.llm.groq import GroqLLMClient
from app.llm.reliability import ConcurrencyLimiter, backoff_seconds, run_with_retries
from app.main import create_app
from tests.conftest import REPO_ROOT


def _groq_settings(**overrides: object) -> Settings:
    payload: dict[str, object] = {
        "llm_provider": "groq",
        "groq_api_key": "gsk_test_not_a_real_key",
        "groq_model": "llama-3.3-70b-versatile",
        "groq_timeout_seconds": 30,
        "groq_max_concurrent_requests": 5,
        "groq_max_retries": 2,
        "data_dir": REPO_ROOT,
    }
    payload.update(overrides)
    return Settings.model_validate(payload)


def _ok_body(content: str = '{"answer": "ok", "evidence_ids": ["ev_france_002"]}') -> dict:
    return {
        "model": "llama-3.3-70b-versatile",
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8},
    }


def test_missing_api_key_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HASAMEX_SKIP_DOTENV", "1")
    monkeypatch.setenv("HASAMEX_LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(LLMConfigError, match="GROQ_API_KEY is not configured"):
        create_provider()


def test_valid_groq_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HASAMEX_SKIP_DOTENV", "1")
    monkeypatch.setenv("HASAMEX_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_not_a_real_key")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("GROQ_MAX_CONCURRENT_REQUESTS", "3")
    settings = load_settings()
    assert settings.llm_provider == "groq"
    assert settings.groq_model == "llama-3.3-70b-versatile"
    assert settings.groq_timeout_seconds == 15
    assert settings.groq_max_concurrent_requests == 3
    assert settings.groq_api_key == "gsk_test_not_a_real_key"


def test_invalid_timeout_is_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HASAMEX_SKIP_DOTENV", "1")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "0")
    with pytest.raises(ConfigError, match="greater than 0"):
        load_settings()


def test_invalid_api_key_is_classified() -> None:
    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        raise LLMAuthenticationError("Groq HTTP 401: invalid key")

    client = GroqLLMClient(_groq_settings(groq_max_retries=2), transport=transport, sleeper=lambda _: None)
    with pytest.raises(LLMAuthenticationError) as exc:
        client.complete([ChatMessage(role="user", content="hi")])
    assert exc.value.code == LLM_AUTHENTICATION_ERROR
    assert exc.value.retryable is False


def test_timeout_is_retried_then_fails() -> None:
    calls = {"n": 0}

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        calls["n"] += 1
        raise LLMTimeout("Groq request timed out.")

    sleeps: list[float] = []
    client = GroqLLMClient(
        _groq_settings(groq_max_retries=2),
        transport=transport,
        sleeper=sleeps.append,
    )
    with pytest.raises(LLMTimeout):
        client.complete([ChatMessage(role="user", content="hi")])
    assert calls["n"] == 3
    assert len(sleeps) == 2
    assert all(delay > 0 for delay in sleeps)


def test_rate_limit_respects_retry_after_then_succeeds() -> None:
    calls = {"n": 0}

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            raise LLMRateLimited("Groq HTTP 429", retry_after=0.01)
        return _ok_body()

    client = GroqLLMClient(_groq_settings(groq_max_retries=2), transport=transport, sleeper=lambda _: None)
    completion = client.complete([ChatMessage(role="user", content="hi")])
    assert calls["n"] == 2
    assert "ev_france_002" in completion.content


def test_transient_failure_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        calls["n"] += 1
        if calls["n"] < 3:
            raise LLMProviderUnavailable("Groq HTTP 503")
        return _ok_body()

    client = GroqLLMClient(_groq_settings(groq_max_retries=2), transport=transport, sleeper=lambda _: None)
    completion = client.complete([ChatMessage(role="user", content="hi")])
    assert calls["n"] == 3
    assert completion.model == "llama-3.3-70b-versatile"


def test_retry_exhaustion_returns_controlled_error() -> None:
    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        raise LLMProviderUnavailable("Groq HTTP 503")

    client = GroqLLMClient(_groq_settings(groq_max_retries=1), transport=transport, sleeper=lambda _: None)
    with pytest.raises(LLMProviderUnavailable) as exc:
        client.complete([ChatMessage(role="user", content="hi")])
    assert exc.value.code == LLM_PROVIDER_UNAVAILABLE


def test_malformed_groq_response_is_rejected() -> None:
    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        return {"choices": []}

    client = GroqLLMClient(_groq_settings(groq_max_retries=0), transport=transport)
    with pytest.raises(LLMInvalidResponse):
        client.complete([ChatMessage(role="user", content="hi")])


def test_empty_groq_content_is_rejected() -> None:
    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        return _ok_body("   ")

    client = GroqLLMClient(_groq_settings(groq_max_retries=0), transport=transport)
    with pytest.raises(LLMInvalidResponse):
        client.complete([ChatMessage(role="user", content="hi")])


def test_prompt_too_large_is_rejected_without_calling_groq() -> None:
    calls = {"n": 0}

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        calls["n"] += 1
        return _ok_body()

    client = GroqLLMClient(_groq_settings(groq_max_prompt_chars=1000), transport=transport)
    with pytest.raises(LLMPromptTooLarge):
        client.complete([ChatMessage(role="user", content="x" * 2000)])
    assert calls["n"] == 0


def test_concurrency_limit() -> None:
    limiter = ConcurrencyLimiter(2)
    current = 0
    peak = 0
    lock = threading.Lock()

    def worker() -> None:
        nonlocal current, peak
        with limiter:
            with lock:
                current += 1
                peak = max(peak, current)
            time.sleep(0.05)
            with lock:
                current -= 1

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert peak <= 2


def test_backoff_uses_retry_after_when_present() -> None:
    delay = backoff_seconds(0, retry_after=1.5, cap=8.0, jitter=False)
    assert delay == 1.5


def test_non_retryable_errors_are_not_retried() -> None:
    calls = {"n": 0}

    def operation() -> str:
        calls["n"] += 1
        raise LLMAuthenticationError("no")

    with pytest.raises(LLMAuthenticationError):
        run_with_retries(operation, max_attempts=4, sleeper=lambda _: None)
    assert calls["n"] == 1


def test_duplicate_request_gate() -> None:
    gate = ExclusiveRequestGate()
    started = threading.Event()
    release = threading.Event()

    def slow() -> str:
        started.set()
        release.wait(timeout=1)
        return "ok"

    first: list[str] = []
    error: list[BaseException] = []

    def run_first() -> None:
        first.append(gate.run("qa:hello", slow))

    thread = threading.Thread(target=run_first)
    thread.start()
    assert started.wait(timeout=1)
    try:
        gate.run("qa:hello", lambda: "nope")
    except LLMDuplicateRequest as exc:
        error.append(exc)
    release.set()
    thread.join()
    assert first == ["ok"]
    assert error and error[0].code == "LLM_DUPLICATE_REQUEST"


def test_api_key_is_redacted_from_logs(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging("INFO")
    with caplog.at_level(logging.INFO):
        log_pipeline(
            "oops",
            authorization="Bearer gsk_abcdefghijklmnopqrstuvwxyz",
            groq="GROQ_API_KEY=gsk_abcdefghijklmnopqrstuvwxyz",
        )
    combined = caplog.text + redact_secrets("Bearer gsk_abcdefghijklmnopqrstuvwxyz")
    assert "gsk_abcdefghijklmnopqrstuvwxyz" not in caplog.text
    assert "[redacted]" in combined


def test_groq_client_does_not_log_authorization_header(caplog: pytest.LogCaptureFixture) -> None:
    configure_logging("INFO")

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        assert headers["Authorization"].startswith("Bearer ")
        return _ok_body()

    client = GroqLLMClient(_groq_settings(), transport=transport)
    with caplog.at_level(logging.INFO):
        client.complete([ChatMessage(role="user", content="hi")])
    assert "gsk_test_not_a_real_key" not in caplog.text
    assert "Authorization" not in caplog.text


def test_groq_failure_does_not_break_transcripts() -> None:
    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        raise LLMProviderUnavailable("Groq HTTP 503")

    provider = GroqLLMClient(_groq_settings(groq_max_retries=0), transport=transport)
    context = build_context(settings=_groq_settings(), provider=provider)
    client = TestClient(create_app(context), raise_server_exceptions=False)
    transcripts = client.get("/api/transcripts")
    assert transcripts.status_code == 200
    assert len(transcripts.json()) == 3
    qa = client.post("/api/qa", json={"question": "What are the purchase timelines?"})
    assert qa.status_code == 200
    body = qa.json()
    quotes = " ".join(item["quote"].lower() for item in body["evidence"])
    assert "six to twelve months" in quotes
    assert "gsk_" not in qa.text


def test_startup_fails_when_groq_selected_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HASAMEX_SKIP_DOTENV", "1")
    monkeypatch.setenv("HASAMEX_LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="GROQ_API_KEY is not configured"):
        create_app()


def test_groq_request_uses_configured_model_and_timeout() -> None:
    seen: dict[str, object] = {}

    def transport(url: str, headers: dict, payload: dict, timeout: float) -> dict:
        seen["url"] = url
        seen["model"] = payload["model"]
        seen["timeout"] = timeout
        seen["max_tokens"] = payload["max_tokens"]
        seen["response_format"] = payload["response_format"]
        seen["user_agent"] = headers.get("User-Agent")
        return _ok_body()

    client = GroqLLMClient(
        _groq_settings(groq_model="llama-3.1-8b-instant", groq_timeout_seconds=12, groq_max_output_tokens=256),
        transport=transport,
    )
    client.complete([ChatMessage(role="system", content="sys"), ChatMessage(role="user", content="hi")])
    assert seen["model"] == "llama-3.1-8b-instant"
    assert seen["timeout"] == 12
    assert seen["max_tokens"] == 256
    assert seen["response_format"] == {"type": "json_object"}
    assert seen["user_agent"] == "Hasamex/0.1"
    assert str(seen["url"]).endswith("/chat/completions")


@pytest.mark.groq_integration
@pytest.mark.groq_env
@pytest.mark.skipif(os.getenv("HASAMEX_GROQ_INTEGRATION") != "1", reason="live Groq calls are opt-in")
def test_live_groq_returns_json_object() -> None:
    from app.core.config import load_dotenv_file

    os.environ.pop("HASAMEX_SKIP_DOTENV", None)
    load_dotenv_file()
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY is not configured")
    os.environ["HASAMEX_LLM_PROVIDER"] = "groq"
    client = GroqLLMClient()
    completion = client.complete(
        [
            ChatMessage(role="system", content="Return JSON with keys answer and evidence_ids."),
            ChatMessage(
                role="user",
                content='{"task":"ping"} Return {"answer":"pong","evidence_ids":[]}',
            ),
        ]
    )
    assert completion.content.strip()
    assert "gsk_" not in completion.content
