"""Immutable evidence model.

Architectural decision:
- Evidence is a copy of an expert utterance, not a model-generated quote.
- The LLM later returns evidence_id values only. The backend resolves
  text, timestamp, expert, and market from this object.
- Interviewer turns never become Evidence. They remain TranscriptSegments.
- frozen=True makes the store the source of truth: callers cannot mutate
  a quote or timestamp after ingest.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Evidence(BaseModel):
    """One expert utterance stored as the canonical source for citations."""

    model_config = ConfigDict(frozen=True)

    evidence_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    speaker: str
    timestamp: str | None
    text: str
