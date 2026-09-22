from app.llm.client import MockLLMProvider
from app.models.analysis import NO_EVIDENCE_ANSWER
from app.services.evidence_store import EvidenceStore
from app.services.qa_service import answer_question
from app.services.retrieval import LexicalRetriever


def test_unsupported_price_question_returns_no_evidence(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    provider = MockLLMProvider(
        [
            {
                "answer": "Robotic systems often cost about two million dollars.",
                "evidence_ids": [],
            }
        ]
    )
    result = answer_question(
        "What is the average price of a robotic surgery system?",
        evidence_store,
        retriever,
        provider,
    )
    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.evidence == []


def test_purchase_timelines_preserve_market_ranges(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    provider = MockLLMProvider(
        [
            {
                "answer": (
                    "France reports 6-12 months, Germany 9-18 months, and the UK "
                    "6-9 months if funding is already available."
                ),
                "evidence_ids": [
                    "ev_france_007",
                    "ev_germany_007",
                    "ev_united_kingdom_006",
                ],
            }
        ]
    )
    result = answer_question(
        "What are the purchase timelines?",
        evidence_store,
        retriever,
        provider,
    )
    joined = " ".join(item.quote.lower() for item in result.evidence)
    assert "six to twelve months" in joined
    assert "nine to eighteen months" in joined
    assert "six to nine months" in joined
    assert {item.market for item in result.evidence} == {
        "France",
        "Germany",
        "United Kingdom",
    }


def test_economics_alone_is_not_universal(
    evidence_store: EvidenceStore, retriever: LexicalRetriever
) -> None:
    provider = MockLLMProvider(
        [
            {
                "answer": (
                    "No. The UK expert describes economics and clinical strategy "
                    "as balanced."
                ),
                "evidence_ids": ["ev_united_kingdom_004", "ev_germany_003"],
            }
        ]
    )
    result = answer_question(
        "Do all experts say economics alone determines purchasing?",
        evidence_store,
        retriever,
        provider,
    )
    assert result.answer.startswith("No.")
    uk = next(item for item in result.evidence if item.market == "United Kingdom")
    assert "economics and clinical strategy are balanced" in uk.quote.lower()
