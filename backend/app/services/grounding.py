"""Ground an LLM answer in retrieved evidence.

Architectural decision:
- If retrieval is empty, the LLM is not called. World knowledge must not
  fill the gap.
- Empty or invalid citations become the canonical no-evidence answer.
  An unsourced model paragraph is discarded.
- Invalid output is retried once, then we fail closed.
"""

from __future__ import annotations

import uuid
from typing import TypeVar

from app.core.logging import log_trace
from app.llm.client import ChatMessage, LLMProvider
from app.llm.prompts import PROMPT_VERSION, build_retry_message
from app.models.analysis import NO_EVIDENCE_ANSWER, AnalysisResponse, QAResponse
from app.models.resolution import PipelineTrace, ResolvedAnswer
from app.services.evidence_store import EvidenceStore
from app.services.resolution import resolve_evidence_ids
from app.services.retrieval import RetrievalHit
from app.services.validation import validate_cited_answer

T = TypeVar("T", AnalysisResponse, QAResponse)


def generate_grounded_answer(
    provider: LLMProvider,
    store: EvidenceStore,
    messages: list[ChatMessage],
    *,
    question: str,
    allowed_ids: set[str],
    retrieved_hits: list[RetrievalHit] | None = None,
    response_model: type[T] = QAResponse,
    request_id: str | None = None,
    max_attempts: int = 2,
) -> ResolvedAnswer:
    request_id = request_id or str(uuid.uuid4())
    retrieved_ids = [hit.evidence.evidence_id for hit in retrieved_hits or []]
    retrieved_scores = [hit.score for hit in retrieved_hits or []]

    if not allowed_ids:
        return _no_evidence(
            request_id=request_id,
            question=question,
            retrieved_ids=retrieved_ids,
            retrieved_scores=retrieved_scores,
            model=provider.model_name,
            validation_result="no_retrieval",
        )

    conversation = list(messages)
    last_error = "invalid model output"
    total_latency = 0.0
    token_usage: dict[str, int | None] = {}

    for attempt in range(max_attempts):
        completion = provider.complete(conversation)
        total_latency += completion.latency_ms
        token_usage = {
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
        }
        result = validate_cited_answer(
            completion.content,
            store,
            model=response_model,
            allowed_ids=allowed_ids,
        )
        if result.ok and result.parsed is not None:
            if not result.valid_ids:
                return _no_evidence(
                    request_id=request_id,
                    question=question,
                    retrieved_ids=retrieved_ids,
                    retrieved_scores=retrieved_scores,
                    model=completion.model,
                    latency_ms=total_latency,
                    token_usage=token_usage,
                    validation_result="empty_citations",
                )
            citations = resolve_evidence_ids(result.valid_ids, store)
            answer = ResolvedAnswer(
                answer=result.parsed.answer,
                evidence=citations,
                evidence_ids=[item.evidence_id for item in citations],
                trace=_trace(
                    request_id=request_id,
                    question=question,
                    retrieved_ids=retrieved_ids,
                    retrieved_scores=retrieved_scores,
                    model=completion.model,
                    latency_ms=total_latency,
                    token_usage=token_usage,
                    validation_result="ok",
                    final_ids=[item.evidence_id for item in citations],
                ),
            )
            if answer.trace is not None:
                log_trace(answer.trace)
            return answer

        last_error = result.error or last_error
        if attempt + 1 < max_attempts:
            conversation = [
                *conversation,
                ChatMessage(role="assistant", content=completion.content),
                build_retry_message(last_error, sorted(allowed_ids)),
            ]

    return _no_evidence(
        request_id=request_id,
        question=question,
        retrieved_ids=retrieved_ids,
        retrieved_scores=retrieved_scores,
        model=provider.model_name,
        latency_ms=total_latency,
        token_usage=token_usage,
        validation_result=f"rejected:{last_error}",
    )


def _no_evidence(
    *,
    request_id: str,
    question: str,
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    model: str,
    validation_result: str,
    latency_ms: float = 0.0,
    token_usage: dict[str, int | None] | None = None,
) -> ResolvedAnswer:
    answer = ResolvedAnswer(
        answer=NO_EVIDENCE_ANSWER,
        evidence=[],
        evidence_ids=[],
        trace=_trace(
            request_id=request_id,
            question=question,
            retrieved_ids=retrieved_ids,
            retrieved_scores=retrieved_scores,
            model=model,
            latency_ms=latency_ms,
            token_usage=token_usage or {},
            validation_result=validation_result,
            final_ids=[],
        ),
    )
    if answer.trace is not None:
        log_trace(answer.trace)
    return answer


def _trace(
    *,
    request_id: str,
    question: str,
    retrieved_ids: list[str],
    retrieved_scores: list[float],
    model: str,
    latency_ms: float,
    token_usage: dict[str, int | None],
    validation_result: str,
    final_ids: list[str],
) -> PipelineTrace:
    return PipelineTrace(
        request_id=request_id,
        question=question,
        retrieved_evidence_ids=retrieved_ids,
        retrieval_scores=retrieved_scores,
        prompt_version=PROMPT_VERSION,
        model=model,
        latency_ms=latency_ms,
        token_usage=token_usage,
        validation_result=validation_result,
        final_evidence_ids=final_ids,
    )
