from app.models.analysis import QAResponse
from app.services.evidence_store import EvidenceStore
from app.services.validation import (
    classify_evidence_ids,
    parse_cited_answer,
    validate_cited_answer,
)


def test_unknown_evidence_id_is_rejected(evidence_store: EvidenceStore) -> None:
    result = validate_cited_answer(
        '{"answer": "Cost is the barrier.", "evidence_ids": ["ev_does_not_exist"]}',
        evidence_store,
        allowed_ids={"ev_france_002"},
    )
    assert result.ok is False
    assert "ev_does_not_exist" in (result.error or "")
    assert result.valid_ids == []


def test_id_not_in_retrieved_set_is_rejected(evidence_store: EvidenceStore) -> None:
    result = validate_cited_answer(
        '{"answer": "Adoption is growing.", "evidence_ids": ["ev_france_001"]}',
        evidence_store,
        allowed_ids={"ev_france_002"},
    )
    assert result.ok is False
    assert "ev_france_001" in result.unknown_ids


def test_hallucinated_quote_field_fails_schema() -> None:
    try:
        parse_cited_answer(
            '{"answer": "x", "evidence_ids": ["ev_france_002"], "quote": "invented"}',
            QAResponse,
        )
    except ValueError as exc:
        assert "schema validation" in str(exc)
    else:
        raise AssertionError("expected schema validation to fail")


def test_valid_ids_pass(evidence_store: EvidenceStore) -> None:
    result = validate_cited_answer(
        '{"answer": "Capital approval is the main issue.", "evidence_ids": ["ev_france_002"]}',
        evidence_store,
        allowed_ids={"ev_france_002", "ev_germany_002"},
    )
    assert result.ok is True
    assert result.valid_ids == ["ev_france_002"]
    assert result.parsed is not None
    assert result.parsed.answer.startswith("Capital approval")


def test_markdown_fenced_json_is_accepted(evidence_store: EvidenceStore) -> None:
    result = validate_cited_answer(
        '```json\n{"answer": "Training matters.", "evidence_ids": ["ev_france_004"]}\n```',
        evidence_store,
        allowed_ids={"ev_france_004"},
    )
    assert result.ok is True


def test_classify_splits_unknown_and_out_of_retrieval(evidence_store: EvidenceStore) -> None:
    classified = classify_evidence_ids(
        ["ev_france_002", "ev_missing", "ev_germany_002"],
        evidence_store,
        allowed_ids={"ev_france_002"},
    )
    assert classified.valid_ids == ["ev_france_002"]
    assert classified.unknown_ids == ["ev_missing"]
    assert classified.out_of_retrieval_ids == ["ev_germany_002"]
