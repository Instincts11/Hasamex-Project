"""Resolve evidence IDs to original quotes and timestamps.

Architectural decision:
- This is the only path from an ID to a displayed quote. Model text is
  never copied into quote or timestamp fields.
- Unknown IDs are omitted, not fabricated. Callers should validate first.
"""

from __future__ import annotations

from app.models.resolution import TIMESTAMP_UNAVAILABLE, ResolvedCitation
from app.services.evidence_store import EvidenceStore


def resolve_evidence_ids(
    evidence_ids: list[str],
    store: EvidenceStore,
) -> list[ResolvedCitation]:
    citations: list[ResolvedCitation] = []
    seen: set[str] = set()
    for evidence_id in evidence_ids:
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        evidence = store.get(evidence_id)
        if evidence is None:
            continue
        citations.append(
            ResolvedCitation(
                evidence_id=evidence.evidence_id,
                transcript_id=evidence.transcript_id,
                expert=evidence.expert,
                role=evidence.role,
                market=evidence.market,
                timestamp=evidence.timestamp,
                timestamp_display=evidence.timestamp or TIMESTAMP_UNAVAILABLE,
                quote=evidence.text,
            )
        )
    return citations
