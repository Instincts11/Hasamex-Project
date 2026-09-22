import pytest
from pydantic import ValidationError

from app.models.analysis import (
    NO_EVIDENCE_ANSWER,
    AnalysisResponse,
    Claim,
    QAResponse,
    Theme,
)


def test_analysis_response_accepts_ids_only() -> None:
    response = AnalysisResponse(
        answer="Economic considerations are a major adoption barrier.",
        evidence_ids=["ev_france_002", "ev_germany_002"],
    )
    assert response.evidence_ids == ["ev_france_002", "ev_germany_002"]
    assert "quote" not in response.model_dump()
    assert "timestamp" not in response.model_dump()


def test_analysis_response_rejects_model_generated_quote() -> None:
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(
            {
                "answer": "Cost is the barrier.",
                "evidence_ids": ["ev_france_002"],
                "quote": "The biggest issue is still capital budget approval.",
            }
        )


def test_qa_response_rejects_timestamp_field() -> None:
    with pytest.raises(ValidationError):
        QAResponse.model_validate(
            {
                "answer": "Timelines differ by market.",
                "evidence_ids": ["ev_france_007"],
                "timestamp": "06:08",
            }
        )


def test_evidence_ids_are_deduplicated_in_order() -> None:
    response = QAResponse(
        answer="Training affects utilisation.",
        evidence_ids=["ev_france_004", "ev_germany_004", "ev_france_004"],
    )
    assert response.evidence_ids == ["ev_france_004", "ev_germany_004"]


def test_no_evidence_response_is_valid() -> None:
    response = QAResponse(answer=NO_EVIDENCE_ANSWER, evidence_ids=[])
    assert response.evidence_ids == []
    assert "provided transcripts" in response.answer


def test_claim_preserves_optional_scope() -> None:
    scoped = Claim(
        topic="procedure-volume growth",
        claim="15 to 20 percent more procedures annually in some stronger centres.",
        scope="France, stronger centres",
        evidence_ids=["ev_france_006"],
    )
    unscoped = Claim(
        topic="procedure-volume growth",
        claim="Growth is gradual because of competing capital priorities.",
        evidence_ids=["ev_germany_005"],
    )
    assert scoped.scope == "France, stronger centres"
    assert unscoped.scope is None


def test_theme_keeps_supporting_and_conflicting_ids_separate() -> None:
    theme = Theme(
        name="Role of economics in purchase decisions",
        summary="France and Germany emphasize the economic case; the UK balances economics and clinical strategy.",
        supporting_evidence_ids=["ev_france_003", "ev_germany_003"],
        conflicting_evidence_ids=["ev_united_kingdom_003"],
    )
    assert "ev_united_kingdom_003" not in theme.supporting_evidence_ids
    assert theme.conflicting_evidence_ids == ["ev_united_kingdom_003"]
