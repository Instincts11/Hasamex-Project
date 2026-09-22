"""In-memory evidence store.

Architectural decision:
- Three transcripts do not need a database. A dict keyed by evidence_id
  is enough and keeps lookup O(1) for later citation resolution.
- The store interface is small so a persistent backend can replace this
  class later without changing analysis contracts.
- Unknown IDs return None. The API layer will reject or retry later;
  this layer does not invent a quote to fill the gap.
- Dedup is exact (transcript_id, timestamp, speaker, text). Semantic
  grouping is an LLM job, not a store job.
"""

from __future__ import annotations

from app.models.evidence import Evidence
from app.models.transcript import TranscriptSegment


class EvidenceStore:
    """Immutable-evidence lookup keyed by deterministic evidence IDs."""

    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}
        self._dedup_keys: set[tuple[str, str | None, str, str]] = set()
        self._counts: dict[str, int] = {}

    def add(self, evidence: Evidence) -> bool:
        """Store evidence. Returns False when an exact duplicate already exists."""
        key = _dedup_key(evidence.transcript_id, evidence.timestamp, evidence.speaker, evidence.text)
        if key in self._dedup_keys or evidence.evidence_id in self._items:
            return False
        self._items[evidence.evidence_id] = evidence
        self._dedup_keys.add(key)
        self._counts[evidence.transcript_id] = self._counts.get(evidence.transcript_id, 0) + 1
        return True

    def get(self, evidence_id: str) -> Evidence | None:
        return self._items.get(evidence_id)

    def get_many(self, evidence_ids: list[str]) -> list[Evidence]:
        found: list[Evidence] = []
        for evidence_id in evidence_ids:
            evidence = self.get(evidence_id)
            if evidence is not None:
                found.append(evidence)
        return found

    def list_all(self) -> list[Evidence]:
        return list(self._items.values())

    def list_by_transcript(self, transcript_id: str) -> list[Evidence]:
        return [item for item in self._items.values() if item.transcript_id == transcript_id]

    def list_by_market(self, market: str) -> list[Evidence]:
        return [item for item in self._items.values() if item.market == market]

    def contains_segment(self, segment: TranscriptSegment) -> bool:
        return _dedup_key(segment.transcript_id, segment.timestamp, segment.speaker, segment.text) in self._dedup_keys

    def next_evidence_id(self, transcript_id: str) -> str:
        next_index = self._counts.get(transcript_id, 0) + 1
        return f"ev_{transcript_id}_{next_index:03d}"

    def clear(self) -> None:
        self._items.clear()
        self._dedup_keys.clear()
        self._counts.clear()

    def __len__(self) -> int:
        return len(self._items)


def _dedup_key(
    transcript_id: str,
    timestamp: str | None,
    speaker: str,
    text: str,
) -> tuple[str, str | None, str, str]:
    return (transcript_id, timestamp, speaker, text)
