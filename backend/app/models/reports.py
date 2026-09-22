"""Display-ready analysis reports.

Architectural decision:
- These objects sit after validation and resolution. Quotes and timestamps
  are already store-backed.
- coverage_label is computed from citation markets, not from the LLM.
  A single-expert theme cannot be labeled as consensus.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.analysis import Claim
from app.models.guide import GuideQuestion
from app.models.resolution import ResolvedAnswer, ResolvedCitation


class ExpertCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)

    expert: str
    market: str
    evidence_ids: list[str] = Field(default_factory=list)


class GuideQuestionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: GuideQuestion
    analysis: ResolvedAnswer
    coverage: list[ExpertCoverage] = Field(default_factory=list)
    coverage_label: str
    experts_covered: int
    experts_total: int


class GuideReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    objective: str
    questions: list[GuideQuestionResult] = Field(default_factory=list)


class ResolvedTheme(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    summary: str
    supporting: list[ResolvedCitation] = Field(default_factory=list)
    conflicting: list[ResolvedCitation] = Field(default_factory=list)
    coverage: list[ExpertCoverage] = Field(default_factory=list)
    coverage_label: str
    single_expert: bool


class ResolvedPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    expert: str
    market: str
    scope: str | None = None
    evidence: list[ResolvedCitation] = Field(default_factory=list)


class ResolvedDifference(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic: str
    summary: str
    positions: list[ResolvedPosition] = Field(default_factory=list)


class ThemeReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    claims: list[Claim] = Field(default_factory=list)
    themes: list[ResolvedTheme] = Field(default_factory=list)
    differences: list[ResolvedDifference] = Field(default_factory=list)
