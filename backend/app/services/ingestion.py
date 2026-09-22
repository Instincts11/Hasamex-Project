"""Transcript ingestion: parse, then store expert utterances as evidence.

Architectural decision:
- Interviewer turns stay on the Transcript for later explorer display.
  They are not evidence, so they never receive an evidence_id.
- Evidence IDs are assigned in file order: ev_{transcript_id}_{nnn}.
  Re-ingest of the same file hits exact-dedup and does not mint new IDs.
- Evidence text is copied from the parsed segment. Ingestion never
  rewrites or summarizes a quote.
"""

from __future__ import annotations

from pathlib import Path

from app.models.evidence import Evidence
from app.models.transcript import Transcript, TranscriptSegment
from app.services.evidence_store import EvidenceStore
from app.services.parser import parse_transcript_file

INTERVIEWER_SPEAKER = "interviewer"


def is_expert_segment(segment: TranscriptSegment) -> bool:
    return segment.speaker.strip().lower() != INTERVIEWER_SPEAKER


def evidence_from_segment(segment: TranscriptSegment, evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        transcript_id=segment.transcript_id,
        expert=segment.expert,
        role=segment.role,
        market=segment.market,
        speaker=segment.speaker,
        timestamp=segment.timestamp,
        text=segment.text,
    )


def ingest_transcript(path: str | Path, store: EvidenceStore) -> Transcript:
    transcript = parse_transcript_file(path)
    for segment in transcript.segments:
        if not is_expert_segment(segment):
            continue
        if store.contains_segment(segment):
            continue
        evidence_id = store.next_evidence_id(segment.transcript_id)
        store.add(evidence_from_segment(segment, evidence_id))
    return transcript
