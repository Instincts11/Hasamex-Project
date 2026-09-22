"""Themes and differences.

Architectural decision:
- Do not ask the LLM for a single vague summary. Claims are extracted
  first, then grouped. Scope stays on the claim.
- After the LLM returns IDs, this service resolves quotes, computes
  coverage, and builds per-market positions. The model cannot relabel
  a single-expert theme as consensus.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Iterable, TypeVar

from pydantic import BaseModel

from app.llm.client import ChatMessage, LLMProvider
from app.llm.prompts import build_claim_messages, build_retry_message, build_theme_messages
from app.models.analysis import (
    Claim,
    ClaimList,
    Difference,
    Theme,
    ThemeAnalysisResponse,
)
from app.models.reports import (
    ResolvedDifference,
    ResolvedPosition,
    ResolvedTheme,
    ThemeReport,
)
from app.services.coverage import coverage_from_citations
from app.services.evidence_store import EvidenceStore
from app.services.resolution import resolve_evidence_ids
from app.services.validation import classify_evidence_ids, parse_model

T = TypeVar("T", bound=BaseModel)


def analyze_themes(
    store: EvidenceStore,
    provider: LLMProvider,
    *,
    max_attempts: int = 2,
) -> ThemeReport:
    evidence = store.list_all()
    allowed_ids = {item.evidence_id for item in evidence}
    if not allowed_ids:
        return ThemeReport()

    claims = _extract_claims(provider, evidence, store, allowed_ids, max_attempts)
    grouping = _group_themes(
        provider,
        claims,
        evidence,
        store,
        allowed_ids,
        max_attempts,
    )
    return _assemble_report(claims, grouping, store)


def _extract_claims(
    provider: LLMProvider,
    evidence: list,
    store: EvidenceStore,
    allowed_ids: set[str],
    max_attempts: int,
) -> list[Claim]:
    parsed = _complete_validated(
        provider,
        build_claim_messages(evidence),
        ClaimList,
        allowed_ids,
        max_attempts=max_attempts,
    )
    if parsed is None:
        return []
    return _sanitize_claims(parsed.claims, store, allowed_ids)


def _group_themes(
    provider: LLMProvider,
    claims: list[Claim],
    evidence: list,
    store: EvidenceStore,
    allowed_ids: set[str],
    max_attempts: int,
) -> ThemeAnalysisResponse:
    if not claims:
        return ThemeAnalysisResponse()
    claims_json = json.dumps(
        [claim.model_dump() for claim in claims],
        ensure_ascii=True,
        indent=2,
    )
    parsed = _complete_validated(
        provider,
        build_theme_messages(claims_json, evidence),
        ThemeAnalysisResponse,
        allowed_ids,
        max_attempts=max_attempts,
    )
    if parsed is None:
        return ThemeAnalysisResponse()
    return _sanitize_theme_analysis(parsed, store, allowed_ids)


def _complete_validated(
    provider: LLMProvider,
    messages: list[ChatMessage],
    model: type[T],
    allowed_ids: set[str],
    max_attempts: int,
) -> T | None:
    conversation = list(messages)
    for attempt in range(max_attempts):
        completion = provider.complete(conversation)
        try:
            return parse_model(completion.content, model)
        except ValueError as exc:
            if attempt + 1 < max_attempts:
                conversation = [
                    *conversation,
                    ChatMessage(role="assistant", content=completion.content),
                    build_retry_message(str(exc), sorted(allowed_ids)),
                ]
    return None


def _sanitize_claims(
    claims: list[Claim],
    store: EvidenceStore,
    allowed_ids: set[str],
) -> list[Claim]:
    cleaned: list[Claim] = []
    for claim in claims:
        valid = classify_evidence_ids(claim.evidence_ids, store, allowed_ids).valid_ids
        if not valid:
            continue
        cleaned.append(claim.model_copy(update={"evidence_ids": valid}))
    return cleaned


def _sanitize_theme_analysis(
    payload: ThemeAnalysisResponse,
    store: EvidenceStore,
    allowed_ids: set[str],
) -> ThemeAnalysisResponse:
    themes: list[Theme] = []
    for theme in payload.themes:
        supporting = classify_evidence_ids(
            theme.supporting_evidence_ids, store, allowed_ids
        ).valid_ids
        conflicting = classify_evidence_ids(
            theme.conflicting_evidence_ids, store, allowed_ids
        ).valid_ids
        if not supporting and not conflicting:
            continue
        themes.append(
            theme.model_copy(
                update={
                    "supporting_evidence_ids": supporting,
                    "conflicting_evidence_ids": conflicting,
                }
            )
        )
    differences: list[Difference] = []
    for difference in payload.differences:
        valid = classify_evidence_ids(difference.evidence_ids, store, allowed_ids).valid_ids
        if not valid:
            continue
        differences.append(difference.model_copy(update={"evidence_ids": valid}))
    return ThemeAnalysisResponse(themes=themes, differences=differences)


def _assemble_report(
    claims: list[Claim],
    grouping: ThemeAnalysisResponse,
    store: EvidenceStore,
) -> ThemeReport:
    themes = [_resolve_theme(theme, store) for theme in grouping.themes]
    differences = [
        _resolve_difference(difference, claims, store) for difference in grouping.differences
    ]
    return ThemeReport(claims=claims, themes=themes, differences=differences)


def _resolve_theme(theme: Theme, store: EvidenceStore) -> ResolvedTheme:
    supporting = resolve_evidence_ids(theme.supporting_evidence_ids, store)
    conflicting = resolve_evidence_ids(theme.conflicting_evidence_ids, store)
    coverage, label, _count, single = coverage_from_citations(supporting + conflicting, store)
    return ResolvedTheme(
        name=theme.name,
        summary=theme.summary,
        supporting=supporting,
        conflicting=conflicting,
        coverage=coverage,
        coverage_label=label,
        single_expert=single,
    )


def _resolve_difference(
    difference: Difference,
    claims: list[Claim],
    store: EvidenceStore,
) -> ResolvedDifference:
    citations = resolve_evidence_ids(difference.evidence_ids, store)
    scope_by_id = _scope_by_evidence_id(claims)
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for citation in citations:
        grouped[(citation.expert, citation.market)].append(citation)
    positions = [
        ResolvedPosition(
            expert=expert,
            market=market,
            scope=_first_scope(items, scope_by_id),
            evidence=items,
        )
        for (expert, market), items in sorted(grouped.items(), key=lambda pair: pair[0][1])
    ]
    return ResolvedDifference(topic=difference.topic, summary=difference.summary, positions=positions)


def _scope_by_evidence_id(claims: list[Claim]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for claim in claims:
        if not claim.scope:
            continue
        for evidence_id in claim.evidence_ids:
            mapping.setdefault(evidence_id, claim.scope)
    return mapping


def _first_scope(citations: Iterable, scope_by_id: dict[str, str]) -> str | None:
    for citation in citations:
        scope = scope_by_id.get(citation.evidence_id)
        if scope:
            return scope
    return None
