"""Replaceable retrieval over the evidence store.

Architectural decision:
- Retrieval is deterministic code behind a Protocol. Phase 2 uses
  lexical TF-IDF over 21 evidence items. A later hybrid or embedding
  retriever can replace LexicalRetriever without changing callers.
- Scores are for ranking and observability only. They are not an
  "AI confidence" metric and must not be shown as such.
- Zero lexical overlap returns an empty list. The retriever does not
  invent a fallback quote.
- A closed synonym list expands only interview-guide vocabulary
  (timeline -> month). It is not a general NLP model.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from app.models.evidence import Evidence
from app.services.evidence_store import EvidenceStore

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "as",
        "at",
        "by",
        "it",
        "its",
        "this",
        "that",
        "with",
        "from",
        "how",
        "what",
        "would",
        "do",
        "does",
        "about",
        "over",
        "next",
        "main",
        "very",
        "your",
        "you",
        "we",
        "they",
        "their",
        "where",
        "who",
        "which",
        "when",
        "can",
        "will",
        "new",
    }
)

# Query-side expansion only. Keys are conservative stems of guide vocabulary.
_QUERY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "timeline": ("month", "cycle"),
    "barrier": ("cost", "funding", "approval"),
    "roi": ("economic", "finance", "utilisation", "utilization"),
    "budget": ("capital", "finance"),
    "disagree": ("balanced", "economic", "clinical", "growth", "percent", "month"),
    "disagreement": ("balanced", "economic", "clinical", "growth", "percent", "month"),
    "differ": ("month", "growth", "economic", "clinical", "balanced"),
}

# Closed exceptions so purchase/purchasing share a token without a full stemmer.
_IRREGULAR_STEMS = {
    "purchasing": "purchase",
    "purchases": "purchase",
    "purchased": "purchase",
}


class RetrievalFilters(BaseModel):
    """Optional metadata filters. Used now so 30+ transcripts do not need a new API."""

    model_config = ConfigDict(frozen=True)

    transcript_id: str | None = None
    market: str | None = None
    expert: str | None = None


class RetrievalHit(BaseModel):
    """Ranked evidence plus a lexical score for logging, not for UI confidence."""

    model_config = ConfigDict(frozen=True)

    evidence: Evidence
    score: float


class Retriever(Protocol):
    def search(self, query: str, top_k: int = 8) -> list[Evidence]:
        ...


class LexicalRetriever:
    """Simple in-memory lexical retriever. No vector index on purpose."""

    def __init__(self, store: EvidenceStore) -> None:
        self._store = store
        self._documents = store.list_all()
        self._tokenized = [tokenize(item.text) for item in self._documents]
        self._idf = _compute_idf(self._tokenized)

    def search(self, query: str, top_k: int = 8) -> list[Evidence]:
        return [hit.evidence for hit in self.search_scored(query, top_k=top_k)]

    def search_scored(
        self,
        query: str,
        top_k: int = 8,
        filters: RetrievalFilters | None = None,
    ) -> list[RetrievalHit]:
        query_terms = expand_query_terms(tokenize(query))
        if not query_terms or top_k <= 0:
            return []

        hits: list[RetrievalHit] = []
        for evidence, tokens in zip(self._documents, self._tokenized, strict=True):
            if not _matches_filters(evidence, filters):
                continue
            score = _score_document(query_terms, tokens, self._idf)
            if score <= 0:
                continue
            hits.append(RetrievalHit(evidence=evidence, score=score))

        hits.sort(key=lambda hit: (-hit.score, hit.evidence.evidence_id))
        return _dedupe_hits(hits)[:top_k]

    def search_per_transcript(
        self,
        query: str,
        per_transcript_k: int = 3,
    ) -> dict[str, list[Evidence]]:
        """Guide workflow helper: retrieve independently from each call."""
        grouped: dict[str, list[Evidence]] = {}
        transcript_ids = {item.transcript_id for item in self._documents}
        for transcript_id in sorted(transcript_ids):
            hits = self.search_scored(
                query,
                top_k=per_transcript_k,
                filters=RetrievalFilters(transcript_id=transcript_id),
            )
            grouped[transcript_id] = [hit.evidence for hit in hits]
        return grouped


def tokenize(text: str) -> list[str]:
    return [
        stem(token)
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def stem(token: str) -> str:
    if token in _IRREGULAR_STEMS:
        return _IRREGULAR_STEMS[token]
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("ly") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def expand_query_terms(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        candidates = (token, *_QUERY_SYNONYMS.get(token, ()))
        for item in candidates:
            normalized = stem(item)
            if normalized in seen:
                continue
            seen.add(normalized)
            expanded.append(normalized)
    return expanded


def _compute_idf(documents: list[list[str]]) -> dict[str, float]:
    doc_count = len(documents)
    df: Counter[str] = Counter()
    for tokens in documents:
        df.update(set(tokens))
    return {
        term: math.log((doc_count + 1) / (count + 1)) + 1.0
        for term, count in df.items()
    }


def _score_document(
    query_terms: list[str],
    doc_tokens: list[str],
    idf: dict[str, float],
) -> float:
    if not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    score = 0.0
    for term in query_terms:
        if term not in tf:
            continue
        score += tf[term] * idf.get(term, 1.0)
    return score


def _matches_filters(evidence: Evidence, filters: RetrievalFilters | None) -> bool:
    if filters is None:
        return True
    if filters.transcript_id and evidence.transcript_id != filters.transcript_id:
        return False
    if filters.market and evidence.market != filters.market:
        return False
    if filters.expert and evidence.expert != filters.expert:
        return False
    return True


def _dedupe_hits(hits: list[RetrievalHit]) -> list[RetrievalHit]:
    seen: set[str] = set()
    unique: list[RetrievalHit] = []
    for hit in hits:
        if hit.evidence.evidence_id in seen:
            continue
        seen.add(hit.evidence.evidence_id)
        unique.append(hit)
    return unique
