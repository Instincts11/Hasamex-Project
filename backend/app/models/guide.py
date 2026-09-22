"""Interview-guide source models. Parsed from Interview_Guide.txt, not invented."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GuideQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int
    text: str


class InterviewGuide(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    objective: str
    questions: list[GuideQuestion] = Field(default_factory=list)
