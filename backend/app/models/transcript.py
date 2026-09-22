"""Transcript models.

Architectural decision:
- TranscriptSegment is every spoken turn, including Interviewer.
  The Transcript Explorer later needs the full call, not just evidence.
- Header fields (expert, role, market) are copied onto every segment so
  a segment is self-contained when retrieved or displayed.
- transcript_id is a slug of the market (france, germany, united_kingdom),
  not a random UUID, so re-ingest of the same file is stable.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TranscriptSegment(BaseModel):
    """One timestamped speaker turn from a parsed transcript."""

    model_config = ConfigDict(frozen=True)

    segment_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    speaker: str
    timestamp: str | None
    text: str


class Transcript(BaseModel):
    """Parsed transcript: header metadata plus every spoken turn."""

    model_config = ConfigDict(frozen=True)

    transcript_id: str
    expert: str
    role: str
    market: str
    source_path: str | None = None
    segments: list[TranscriptSegment] = Field(default_factory=list)
