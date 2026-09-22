from app.llm.client import MockLLMProvider
from app.models.guide import GuideQuestion
from app.services.evidence_store import EvidenceStore
from app.services.guide_service import analyze_guide_question, retrieve_per_transcript
from app.services.retrieval import LexicalRetriever


def test_guide_retrieval_covers_each_market_for_barriers(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    hits = retrieve_per_transcript(
        retriever, evidence_store, "What are the main barriers to adoption?"
    )
    markets = {hit.evidence.market for hit in hits}
    texts = " ".join(hit.evidence.text.lower() for hit in hits)
    assert markets == {"France", "Germany", "United Kingdom"}
    assert "capital budget approval" in texts
    assert "cost is the first barrier" in texts


def test_guide_retrieval_covers_all_three_timelines(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    hits = retrieve_per_transcript(
        retriever,
        evidence_store,
        "What is the typical hospital decision-making timeline for purchasing a new robotic system?",
    )
    joined = " ".join(hit.evidence.text.lower() for hit in hits)
    assert "six to twelve months" in joined
    assert "nine to eighteen months" in joined
    assert "six to nine months" in joined


def test_guide_question_resolves_barrier_quotes(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    provider = MockLLMProvider(
        [
            {
                "answer": (
                    "France cites capital budget approval, Germany cites cost, "
                    "and the UK treats funding and training capacity as equally important."
                ),
                "evidence_ids": [
                    "ev_france_002",
                    "ev_germany_002",
                    "ev_united_kingdom_002",
                ],
            }
        ]
    )
    result = analyze_guide_question(
        GuideQuestion(number=2, text="What are the main barriers to adoption?"),
        evidence_store,
        retriever,
        provider,
    )
    quotes = " ".join(item.quote.lower() for item in result.analysis.evidence)
    assert result.experts_covered == 3
    assert result.coverage_label == "3/3 experts"
    assert "capital budget approval" in quotes
    assert "cost is the first barrier" in quotes
    assert result.analysis.evidence[0].timestamp == "01:20"
