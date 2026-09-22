import re

from app.services.evidence_store import EvidenceStore
from app.services.retrieval import LexicalRetriever, RetrievalFilters


def test_barrier_query_retrieves_economic_barriers(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("What are the main barriers to adoption?", top_k=8)
    joined = " ".join(item.text.lower() for item in hits)

    assert any("capital budget approval" in item.text.lower() for item in hits)
    assert any("cost is the first barrier" in item.text.lower() for item in hits)
    assert "funding is important" in joined
    assert {item.market for item in hits} >= {"France", "Germany", "United Kingdom"}


def test_timeline_query_retrieves_all_three_ranges(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("What are the purchase timelines?", top_k=8)
    joined = " ".join(item.text.lower() for item in hits)

    assert "six to twelve months" in joined
    assert "nine to eighteen months" in joined
    assert "six to nine months" in joined


def test_training_query_is_relevant(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("How important are surgeon training and utilisation?", top_k=8)
    joined = " ".join(item.text.lower() for item in hits)

    assert "training matters" in joined
    assert "only one surgeon" in joined


def test_unrelated_query_returns_no_evidence(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    assert retriever.search("photovoltaic satellite launch window") == []


def test_price_query_does_not_surface_a_price(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("What is the average price of a robotic surgery system?")
    price_pattern = re.compile(r"€|\$|\bprice\b|\busd\b|\beur\b|\bavg\b", re.IGNORECASE)
    for item in hits:
        assert price_pattern.search(item.text) is None


def test_market_filter_limits_results(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search_scored(
        "adoption",
        top_k=8,
        filters=RetrievalFilters(market="France"),
    )
    assert hits
    assert all(hit.evidence.market == "France" for hit in hits)


def test_search_per_transcript_covers_each_call(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    grouped = retriever.search_per_transcript("training", per_transcript_k=2)
    assert set(grouped) == {"france", "germany", "united_kingdom"}
    assert all(len(items) <= 2 for items in grouped.values())
    assert any("training" in item.text.lower() for item in grouped["france"])


def test_retrieval_does_not_return_duplicate_ids(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("hospital capital budget utilisation training", top_k=12)
    ids = [item.evidence_id for item in hits]
    assert ids == list(dict.fromkeys(ids))


def test_zero_top_k_returns_empty(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    assert retriever.search("adoption", top_k=0) == []


def test_disagreement_query_retrieves_cross_market_positions(
    evidence_store: EvidenceStore,
) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("Where do experts disagree?", top_k=10)
    joined = " ".join(item.text.lower() for item in hits)
    assert hits
    assert {item.market for item in hits} >= {"France", "Germany", "United Kingdom"}
    assert "balanced" in joined or "economic" in joined
    assert "growth" in joined or "percent" in joined or "month" in joined
