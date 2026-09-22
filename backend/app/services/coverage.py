"""Coverage labels computed from resolved citations.

Architectural decision:
- Coverage is deterministic. The LLM cannot declare a single-expert
  theme to be cross-expert consensus.
"""

from __future__ import annotations

from collections import defaultdict

from app.models.reports import ExpertCoverage
from app.models.resolution import ResolvedCitation
from app.services.evidence_store import EvidenceStore


def store_expert_total(store: EvidenceStore) -> int:
    return len({item.expert for item in store.list_all()})


def coverage_from_citations(
    citations: list[ResolvedCitation],
    store: EvidenceStore,
) -> tuple[list[ExpertCoverage], str, int, bool]:
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for item in citations:
        grouped[(item.expert, item.market)].append(item.evidence_id)

    coverage = [
        ExpertCoverage(expert=expert, market=market, evidence_ids=ids)
        for (expert, market), ids in sorted(grouped.items(), key=lambda pair: pair[0][1])
    ]
    experts_covered = len(coverage)
    experts_total = store_expert_total(store)
    single_expert = experts_covered == 1
    if experts_covered == 0:
        label = "No expert coverage"
    elif single_expert:
        label = f"Single-expert evidence ({coverage[0].market})"
    else:
        label = f"{experts_covered}/{experts_total} experts"
    return coverage, label, experts_covered, single_expert
