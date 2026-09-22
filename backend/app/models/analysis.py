"""LLM output contracts for later analysis workflows.

Architectural decision:
- These models are what the LLM is allowed to return. They contain
  answers and evidence_id lists, never quotes or timestamps.
- extra='forbid' rejects model-generated source metadata. If a provider
  sneaks quote/timestamp/expert fields into JSON, validation fails and
  the backend does not display hallucinated provenance.
- Duplicate evidence IDs are dropped in order. Dedup is deterministic
  here so later display code does not have to guess.
- QAResponse and AnalysisResponse stay separate types so guide analysis
  and free-form Q&A can evolve independently.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

NO_EVIDENCE_ANSWER = (
    "No supporting evidence was found in the provided transcripts."
)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


class AnalysisResponse(BaseModel):
    """Structured guide-question answer. Quotes are resolved from IDs later."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids")
    @classmethod
    def _dedupe_evidence_ids(cls, value: list[str]) -> list[str]:
        return _dedupe_preserve_order(value)


class QAResponse(BaseModel):
    """Structured cross-transcript Q&A answer. Same ID-only citation rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids")
    @classmethod
    def _dedupe_evidence_ids(cls, value: list[str]) -> list[str]:
        return _dedupe_preserve_order(value)


class Claim(BaseModel):
    """One expert observation. Scope stays on the claim, not the theme."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    topic: str
    claim: str
    scope: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids")
    @classmethod
    def _dedupe_evidence_ids(cls, value: list[str]) -> list[str]:
        return _dedupe_preserve_order(value)


class Theme(BaseModel):
    """Grouped claims. Same topic is not automatically consensus."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    summary: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    conflicting_evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("supporting_evidence_ids", "conflicting_evidence_ids")
    @classmethod
    def _dedupe_evidence_ids(cls, value: list[str]) -> list[str]:
        return _dedupe_preserve_order(value)


class ClaimList(BaseModel):
    """LLM claim-extraction payload. Scope stays on each claim."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    claims: list[Claim] = Field(default_factory=list)


class Difference(BaseModel):
    """A scoped divergence, not automatically a contradiction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    topic: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids")
    @classmethod
    def _dedupe_evidence_ids(cls, value: list[str]) -> list[str]:
        return _dedupe_preserve_order(value)


class ThemeAnalysisResponse(BaseModel):
    """LLM theme-grouping payload. IDs only; quotes are resolved later."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    themes: list[Theme] = Field(default_factory=list)
    differences: list[Difference] = Field(default_factory=list)
