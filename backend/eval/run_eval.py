"""Run the golden set. Metrics measure evidence quality, not model confidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from app.llm.extractive import ExtractiveLLMProvider
from app.models.analysis import NO_EVIDENCE_ANSWER
from app.services.evidence_store import EvidenceStore
from app.services.ingestion import ingest_transcript
from app.services.qa_service import answer_question
from app.services.retrieval import LexicalRetriever

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = Path(__file__).resolve().parent / "golden_set.json"
TRANSCRIPTS = [
    REPO_ROOT / "Transcript_1_France.txt",
    REPO_ROOT / "Transcript_2_Germany.txt",
    REPO_ROOT / "Transcript_3_UK.txt",
]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def score_case(
    case: dict[str, Any],
    retrieved_ids: list[str],
    result,
    store: EvidenceStore,
) -> dict[str, Any]:
    relevant = set(case["relevant_ids"])
    required = set(case["required_ids"])
    retrieved = set(retrieved_ids)
    cited = set(result.evidence_ids)
    joined_quotes = " ".join(item.quote for item in result.evidence).lower()
    answer = result.answer.lower()

    quote_matches = 0
    for citation in result.evidence:
        source = store.get(citation.evidence_id)
        if source is not None and citation.quote == source.text:
            quote_matches += 1

    required_quotes = case["required_quote_substrings"]
    substring_hits = sum(1 for item in required_quotes if item.lower() in joined_quotes)
    forbidden = [
        item
        for item in case.get("forbidden_answer_substrings", [])
        if item.lower() in answer
    ]
    cited_markets = {item.market for item in result.evidence}
    expected_markets = set(case["expected_markets"])

    no_evidence_ok = True
    if case["expect_no_evidence"]:
        no_evidence_ok = result.answer == NO_EVIDENCE_ANSWER and not result.evidence

    grounded = (
        no_evidence_ok
        and quote_matches == len(result.evidence)
        and not forbidden
    )
    id_complete = _ratio(len(cited & required), len(required))
    quote_complete = _ratio(substring_hits, len(required_quotes))
    completeness = (id_complete + quote_complete) / 2

    return {
        "id": case["id"],
        "question": case["question"],
        "retrieval_precision": _ratio(len(retrieved & relevant), len(retrieved)),
        "retrieval_recall": _ratio(len(retrieved & relevant), len(relevant)),
        "citation_accuracy": _ratio(len(cited & relevant), len(cited)),
        "quote_accuracy": _ratio(quote_matches, len(result.evidence)),
        "groundedness": 1.0 if grounded else 0.0,
        "evidence_coverage": _ratio(len(cited_markets & expected_markets), len(expected_markets)),
        "completeness": completeness,
        "retrieved_ids": retrieved_ids,
        "cited_ids": result.evidence_ids,
        "validation_result": result.trace.validation_result if result.trace else None,
        "model": result.trace.model if result.trace else None,
        "forbidden_hits": forbidden,
    }


def load_corpus() -> tuple[EvidenceStore, LexicalRetriever]:
    store = EvidenceStore()
    for path in TRANSCRIPTS:
        ingest_transcript(path, store)
    return store, LexicalRetriever(store)


def run_eval(provider=None) -> dict[str, Any]:
    spec = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    store, retriever = load_corpus()
    llm = provider or ExtractiveLLMProvider()
    rows = []
    for case in spec["cases"]:
        hits = retriever.search_scored(case["question"], top_k=10)
        result = answer_question(case["question"], store, retriever, llm)
        rows.append(
            score_case(case, [hit.evidence.evidence_id for hit in hits], result, store)
        )

    metric_names = [
        "retrieval_precision",
        "retrieval_recall",
        "citation_accuracy",
        "quote_accuracy",
        "groundedness",
        "evidence_coverage",
        "completeness",
    ]
    summary = {name: round(mean(row[name] for row in rows), 3) for name in metric_names}
    return {"summary": summary, "cases": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Hasamex golden evaluation.")
    parser.parse_args()
    report = run_eval()
    print(json.dumps(report, indent=2))
    print("\nSummary (not a confidence score):")
    for key, value in report["summary"].items():
        print(f"  {key}: {value:.3f}")


if __name__ == "__main__":
    main()
