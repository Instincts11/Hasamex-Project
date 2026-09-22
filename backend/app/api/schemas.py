"""HTTP DTOs. Quotes and timestamps are copied from resolved store objects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.resolution import ResolvedCitation


class EvidenceOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    timestamp: str
    quote: str


class AnswerOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str
    evidence: list[EvidenceOut] = Field(default_factory=list)


class QARequest(BaseModel):
    question: str


class GuideAnalyzeRequest(BaseModel):
    question_number: int | None = None


class TranscriptSummaryOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    transcript_id: str
    expert: str
    role: str
    market: str
    segment_count: int
    evidence_count: int


class SegmentOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    segment_id: str
    speaker: str
    timestamp: str | None
    timestamp_display: str
    text: str


class TranscriptDetailOut(TranscriptSummaryOut):
    segments: list[SegmentOut] = Field(default_factory=list)


class IngestOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    transcript_count: int
    evidence_count: int
    experts: list[str]


class CorpusOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    expert_count: int
    evidence_count: int
    transcript_count: int
    guide_question_count: int
    provider: str
    transcripts: list[TranscriptSummaryOut] = Field(default_factory=list)


class GuideQuestionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    text: str


class GuideOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    objective: str
    questions: list[GuideQuestionOut] = Field(default_factory=list)


class CoverageOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    expert: str
    market: str
    evidence_ids: list[str] = Field(default_factory=list)


class GuideQuestionResultOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    question: str
    answer: str
    evidence: list[EvidenceOut] = Field(default_factory=list)
    coverage: list[CoverageOut] = Field(default_factory=list)
    coverage_label: str
    experts_covered: int
    experts_total: int


class GuideReportOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    objective: str
    questions: list[GuideQuestionResultOut] = Field(default_factory=list)


class ThemeOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    summary: str
    coverage_label: str
    single_expert: bool
    supporting: list[EvidenceOut] = Field(default_factory=list)
    conflicting: list[EvidenceOut] = Field(default_factory=list)


class PositionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    expert: str
    market: str
    scope: str | None = None
    evidence: list[EvidenceOut] = Field(default_factory=list)


class DifferenceOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic: str
    summary: str
    positions: list[PositionOut] = Field(default_factory=list)


class ThemesOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    themes: list[ThemeOut] = Field(default_factory=list)


class DifferencesOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    differences: list[DifferenceOut] = Field(default_factory=list)


def evidence_out(citation: ResolvedCitation) -> EvidenceOut:
    return EvidenceOut(
        evidence_id=citation.evidence_id,
        transcript_id=citation.transcript_id,
        expert=citation.expert,
        role=citation.role,
        market=citation.market,
        timestamp=citation.timestamp_display,
        quote=citation.quote,
    )