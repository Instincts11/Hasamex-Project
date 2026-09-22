"""Runtime settings from environment variables.

Architectural decision:
- API keys are never hardcoded. Tests run without a credential.
- Groq is selected when GROQ_API_KEY is present unless HASAMEX_LLM_PROVIDER
  is set explicitly. Missing Groq config fails clearly when groq is selected.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


class ConfigError(ValueError):
    """Invalid environment configuration. Never include secrets in the message."""


DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_CORS = ("http://localhost:3000", "http://127.0.0.1:3000")
BACKEND_DIR = Path(__file__).resolve().parents[2]


def default_data_dir() -> Path:
    env = os.getenv("HASAMEX_DATA_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)

    llm_provider: str
    llm_api_key: str | None = None
    llm_model: str = DEFAULT_OPENAI_MODEL
    llm_base_url: str = DEFAULT_OPENAI_BASE_URL
    groq_api_key: str | None = None
    groq_model: str = DEFAULT_GROQ_MODEL
    groq_base_url: str = DEFAULT_GROQ_BASE_URL
    groq_timeout_seconds: float = 30.0
    groq_max_concurrent_requests: int = 5
    groq_max_retries: int = 2
    groq_retry_base_seconds: float = 0.4
    groq_max_prompt_chars: int = 24000
    groq_max_output_tokens: int = 1024
    retrieval_top_k: int = 10
    data_dir: Path
    cors_origins: tuple[str, ...] = DEFAULT_CORS
    log_level: str = "INFO"

    @field_validator("llm_provider")
    @classmethod
    def _provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"mock", "openai", "groq"}:
            raise ValueError(f"Unknown HASAMEX_LLM_PROVIDER: {value}")
        return normalized

    @field_validator("groq_model")
    @classmethod
    def _model_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("GROQ_MODEL must not be empty.")
        return value.strip()

    @field_validator("groq_timeout_seconds", "groq_retry_base_seconds")
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Timeout and retry base must be greater than 0.")
        return value

    @field_validator("groq_max_concurrent_requests", "retrieval_top_k", "groq_max_output_tokens")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Concurrency, retrieval top_k, and max output tokens must be at least 1.")
        return value

    @field_validator("groq_max_retries")
    @classmethod
    def _retries(cls, value: int) -> int:
        if value < 0 or value > 5:
            raise ValueError("GROQ_MAX_RETRIES must be between 0 and 5.")
        return value

    @field_validator("groq_max_prompt_chars")
    @classmethod
    def _prompt_chars(cls, value: int) -> int:
        if value < 1000:
            raise ValueError("GROQ_MAX_PROMPT_CHARS is too small.")
        return value

    def require_groq_key(self) -> None:
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ConfigError(
                "Configuration error:\n"
                "GROQ_API_KEY is not configured.\n"
                "Create a .env file and provide the Groq API key."
            )


def load_dotenv_file(path: Path | None = None) -> None:
    """Load backend/.env without overriding already-set environment variables."""
    if os.getenv("HASAMEX_SKIP_DOTENV") == "1":
        return
    env_path = path or (BACKEND_DIR / ".env")
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _strip_env_value(value)


def load_settings() -> Settings:
    load_dotenv_file()
    groq_key = _first_env("GROQ_API_KEY")
    cors = os.getenv("HASAMEX_CORS_ORIGINS")
    try:
        settings = Settings(
            llm_provider=_resolve_provider(groq_key),
            llm_api_key=_first_env("OPENAI_API_KEY", "HASAMEX_LLM_API_KEY"),
            llm_model=os.getenv("HASAMEX_LLM_MODEL", DEFAULT_OPENAI_MODEL),
            llm_base_url=os.getenv("HASAMEX_LLM_BASE_URL", DEFAULT_OPENAI_BASE_URL).rstrip("/"),
            groq_api_key=groq_key,
            groq_model=os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
            groq_base_url=os.getenv("GROQ_BASE_URL", DEFAULT_GROQ_BASE_URL).rstrip("/"),
            groq_timeout_seconds=_env_float("GROQ_TIMEOUT_SECONDS", 30.0),
            groq_max_concurrent_requests=_env_int("GROQ_MAX_CONCURRENT_REQUESTS", 5),
            groq_max_retries=_env_int("GROQ_MAX_RETRIES", 2),
            groq_retry_base_seconds=_env_float("GROQ_RETRY_BASE_SECONDS", 0.4),
            groq_max_prompt_chars=_env_int("GROQ_MAX_PROMPT_CHARS", 24000),
            groq_max_output_tokens=_env_int("GROQ_MAX_OUTPUT_TOKENS", 1024),
            retrieval_top_k=_env_int("HASAMEX_RETRIEVAL_TOP_K", 10),
            data_dir=default_data_dir(),
            cors_origins=tuple(item.strip() for item in cors.split(",") if item.strip())
            if cors
            else DEFAULT_CORS,
            log_level=os.getenv("HASAMEX_LOG_LEVEL", "INFO"),
        )
    except ValidationError as exc:
        raise ConfigError(_format_settings_error(exc)) from exc
    return settings


def _resolve_provider(groq_key: str | None) -> str:
    explicit = os.getenv("HASAMEX_LLM_PROVIDER")
    if explicit is not None and explicit.strip():
        return explicit.strip().lower()
    if groq_key:
        return "groq"
    return "mock"


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer.") from exc


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number.") from exc


def _strip_env_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _format_settings_error(exc: ValidationError) -> str:
    parts = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error.get("loc", ()))
        parts.append(f"{location}: {error.get('msg')}")
    return "Configuration error:\n" + "\n".join(parts)
