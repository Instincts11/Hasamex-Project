"""Resolved, display-ready answers.

Architectural decision:
- quote and timestamp always come from the evidence store, never from
  model output. This object is what the API/UI may show.
- timestamp_display is "Timestamp unavailable." when the source has none.
  We do not invent a neighboring time.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

TIMESTAMP_UNAVAILABLE = "Timestamp unavailable."


class ResolvedCitation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    timestamp: str | None
    timestamp_display: str
    quote: str


class PipelineTrace(BaseModel):
    """Observability record for one grounded generation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    question: str
    retrieved_evidence_ids: list[str] = Field(default_factory=list)
    retrieval_scores: list[float] = Field(default_factory=list)
    prompt_version: str
    model: str
    latency_ms: float = 0.0
    token_usage: dict[str, int | None] = Field(default_factory=dict)
    validation_result: str
    final_evidence_ids: list[str] = Field(default_factory=list)


class ResolvedAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    evidence: list[ResolvedCitation] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    trace: PipelineTrace | None = None
