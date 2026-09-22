from app.models.resolution import TIMESTAMP_UNAVAILABLE
from app.services.evidence_store import EvidenceStore
from app.services.ingestion import ingest_transcript
from app.services.resolution import resolve_evidence_ids

from tests.conftest import FIXTURES_DIR

FRANCE_01_20 = (
    "The biggest issue is still capital budget approval. "
    "Hospitals may like the technology clinically, but purchasing "
    "committees need a strong economic case before approving a system."
)


def test_resolves_exact_france_quote(evidence_store: EvidenceStore) -> None:
    citations = resolve_evidence_ids(["ev_france_002"], evidence_store)
    assert len(citations) == 1
    assert citations[0].quote == FRANCE_01_20
    assert citations[0].timestamp == "01:20"
    assert citations[0].timestamp_display == "01:20"
    assert citations[0].expert == "Dr. Jean Martin"
    assert citations[0].market == "France"
    assert citations[0].transcript_id == "france"


def test_never_uses_a_caller_supplied_quote(evidence_store: EvidenceStore) -> None:
    citations = resolve_evidence_ids(["ev_france_002"], evidence_store)
    assert "invented" not in citations[0].quote
    assert citations[0].quote == evidence_store.get("ev_france_002").text


def test_missing_timestamp_displays_unavailable() -> None:
    store = EvidenceStore()
    ingest_transcript(FIXTURES_DIR / "missing_timestamp.txt", store)
    citations = resolve_evidence_ids(["ev_testland_001"], store)
    assert citations[0].timestamp is None
    assert citations[0].timestamp_display == TIMESTAMP_UNAVAILABLE
    assert citations[0].quote == "Expert answer with no timestamp."


def test_unknown_id_is_omitted_not_invented(evidence_store: EvidenceStore) -> None:
    citations = resolve_evidence_ids(["ev_france_002", "ev_does_not_exist"], evidence_store)
    assert [item.evidence_id for item in citations] == ["ev_france_002"]


def test_duplicate_ids_resolve_once(evidence_store: EvidenceStore) -> None:
    citations = resolve_evidence_ids(
        ["ev_france_002", "ev_france_002", "ev_germany_002"],
        evidence_store,
    )
    assert [item.evidence_id for item in citations] == ["ev_france_002", "ev_germany_002"]
