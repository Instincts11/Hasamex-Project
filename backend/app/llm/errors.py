"""Application-level LLM error categories.

Architectural decision:
- Groq/SDK exceptions never reach the frontend. They are mapped to
  stable codes the UI can display without leaking internals.
- User-facing messages must not include keys, headers, or stack traces.
"""

from __future__ import annotations

LLM_CONFIGURATION_ERROR = "LLM_CONFIGURATION_ERROR"
LLM_AUTHENTICATION_ERROR = "LLM_AUTHENTICATION_ERROR"
LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
LLM_TIMEOUT = "LLM_TIMEOUT"
LLM_PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
LLM_CONNECTION_ERROR = "LLM_CONNECTION_ERROR"
LLM_INVALID_RESPONSE = "LLM_INVALID_RESPONSE"
LLM_VALIDATION_ERROR = "LLM_VALIDATION_ERROR"
LLM_DUPLICATE_REQUEST = "LLM_DUPLICATE_REQUEST"
LLM_PROMPT_TOO_LARGE = "LLM_PROMPT_TOO_LARGE"
LLM_UNKNOWN_ERROR = "LLM_UNKNOWN_ERROR"

UNAVAILABLE_MESSAGE = (
    "AI analysis is temporarily unavailable. "
    "Your transcripts and source evidence are still accessible. "
    "Please try again shortly."
)


class LLMError(RuntimeError):
    """Provider or transport failure with a stable application code."""

    code = LLM_UNKNOWN_ERROR
    http_status = 503
    user_message = UNAVAILABLE_MESSAGE

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        http_status: int | None = None,
        user_message: str | None = None,
        retry_after: float | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message or user_message or self.user_message)
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        if user_message is not None:
            self.user_message = user_message
        self.retry_after = retry_after
        self.retryable = self._default_retryable() if retryable is None else retryable

    def _default_retryable(self) -> bool:
        return self.code in {
            LLM_RATE_LIMITED,
            LLM_TIMEOUT,
            LLM_PROVIDER_UNAVAILABLE,
            LLM_CONNECTION_ERROR,
        }


class LLMConfigError(LLMError):
    code = LLM_CONFIGURATION_ERROR
    http_status = 500
    user_message = "The AI service is not configured."

    def _default_retryable(self) -> bool:
        return False


class LLMAuthenticationError(LLMError):
    code = LLM_AUTHENTICATION_ERROR
    http_status = 502
    user_message = UNAVAILABLE_MESSAGE

    def _default_retryable(self) -> bool:
        return False


class LLMRateLimited(LLMError):
    code = LLM_RATE_LIMITED
    http_status = 429
    user_message = "The AI service is busy. Please try again shortly."


class LLMTimeout(LLMError):
    code = LLM_TIMEOUT
    http_status = 504
    user_message = UNAVAILABLE_MESSAGE


class LLMProviderUnavailable(LLMError):
    code = LLM_PROVIDER_UNAVAILABLE
    http_status = 503
    user_message = UNAVAILABLE_MESSAGE


class LLMConnectionError(LLMError):
    code = LLM_CONNECTION_ERROR
    http_status = 503
    user_message = UNAVAILABLE_MESSAGE


class LLMInvalidResponse(LLMError):
    code = LLM_INVALID_RESPONSE
    http_status = 502
    user_message = UNAVAILABLE_MESSAGE

    def _default_retryable(self) -> bool:
        return False


class LLMValidationError(LLMError):
    code = LLM_VALIDATION_ERROR
    http_status = 502
    user_message = UNAVAILABLE_MESSAGE

    def _default_retryable(self) -> bool:
        return False


class LLMDuplicateRequest(LLMError):
    code = LLM_DUPLICATE_REQUEST
    http_status = 409
    user_message = "This analysis request is already in progress."

    def _default_retryable(self) -> bool:
        return False


class LLMPromptTooLarge(LLMError):
    code = LLM_PROMPT_TOO_LARGE
    http_status = 400
    user_message = "The request is too large to send to the AI service."

    def _default_retryable(self) -> bool:
        return False


def classify_http_status(status: int) -> type[LLMError]:
    if status in {401, 403}:
        return LLMAuthenticationError
    if status == 429:
        return LLMRateLimited
    if status in {408, 504}:
        return LLMTimeout
    if status >= 500:
        return LLMProviderUnavailable
    if status >= 400:
        return LLMInvalidResponse
    return LLMError


def groq_key_missing_message() -> str:
    return (
        "Configuration error:\n"
        "GROQ_API_KEY is not configured.\n"
        "Create a .env file and provide the Groq API key."
    )
