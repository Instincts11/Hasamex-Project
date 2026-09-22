from fastapi.testclient import TestClient

from app.api.state import build_context
from app.llm.errors import LLMRateLimited
from app.main import create_app
from app.models.analysis import NO_EVIDENCE_ANSWER
from app.services.evidence_store import EvidenceStore


def _client() -> TestClient:
    return TestClient(create_app(build_context()), raise_server_exceptions=True)


def test_health_and_transcript_list() -> None:
    client = _client()
    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.json()
    assert body["transcript_count"] == 3
    assert body["evidence_count"] == 21
    assert body["guide_question_count"] == 0
    assert "GROQ_API_KEY" not in health.text
    assert "gsk_" not in health.text

    root_health = client.get("/health")
    assert root_health.status_code == 200
    assert root_health.json()["status"] == "ok"
    assert "llm_provider" in root_health.json()
    assert "GROQ_API_KEY" not in root_health.text
    assert "gsk_" not in root_health.text

    listing = client.get("/api/transcripts")
    assert {item["market"] for item in listing.json()} == {
        "France",
        "Germany",
        "United Kingdom",
    }


def test_get_france_transcript_includes_segments() -> None:
    client = _client()
    response = client.get("/api/transcripts/france")
    assert response.status_code == 200
    body = response.json()
    assert body["expert"] == "Dr. Jean Martin"
    assert body["segment_count"] == 14
    assert body["segments"][0]["speaker"] == "Interviewer"
    assert body["segments"][1]["timestamp"] == "00:18"


def test_unknown_transcript_is_404() -> None:
    client = _client()
    assert client.get("/api/transcripts/spain").status_code == 404


def test_ingest_reloads_the_same_corpus() -> None:
    client = _client()
    response = client.post("/api/transcripts/ingest")
    assert response.status_code == 200
    assert response.json()["evidence_count"] == 21
    assert len(response.json()["experts"]) == 3


def test_qa_price_question_is_grounded_no_evidence() -> None:
    client = _client()
    response = client.post(
        "/api/qa",
        json={"question": "What is the average price of a robotic surgery system?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == NO_EVIDENCE_ANSWER
    assert body["evidence"] == []


def test_qa_timelines_resolve_store_quotes() -> None:
    client = _client()
    response = client.post("/api/qa", json={"question": "What are the purchase timelines?"})
    assert response.status_code == 200
    quotes = " ".join(item["quote"].lower() for item in response.json()["evidence"])
    assert "six to twelve months" in quotes
    assert "nine to eighteen months" in quotes
    assert "six to nine months" in quotes
    france = next(item for item in response.json()["evidence"] if item["market"] == "France")
    store = EvidenceStore()
    from app.services.ingestion import ingest_transcript
    from tests.conftest import FRANCE_TRANSCRIPT

    ingest_transcript(FRANCE_TRANSCRIPT, store)
    assert france["quote"] == store.get("ev_france_007").text
    assert france["timestamp"] == "06:08"


def test_guide_question_is_unavailable_without_source_file() -> None:
    client = _client()
    response = client.post("/api/analysis/guide", json={"question_number": 2})
    assert response.status_code == 404


def test_themes_and_differences_use_store_quotes() -> None:
    client = _client()
    themes = client.get("/api/analysis/themes")
    assert themes.status_code == 200
    theme_body = themes.json()["themes"]
    assert theme_body
    supporting = [item for theme in theme_body for item in theme["supporting"]]
    assert all(item["quote"] for item in supporting)
    assert any(item["timestamp"] != "Timestamp unavailable." for item in supporting)

    differences = client.get("/api/analysis/differences")
    assert differences.status_code == 200
    diff_body = differences.json()["differences"]
    assert diff_body
    markets = {
        position["market"]
        for item in diff_body
        for position in item["positions"]
    }
    assert len(markets) >= 2


def test_theme_rate_limit_cools_down_and_sends_retry_after() -> None:
    class RateLimitedProvider:
        model_name = "mock"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, messages: object) -> None:
            del messages
            self.calls += 1
            raise LLMRateLimited("Groq HTTP 429", retry_after=12)

    provider = RateLimitedProvider()
    context = build_context(provider=provider)
    client = TestClient(create_app(context), raise_server_exceptions=False)
    first = client.get("/api/analysis/themes")
    assert first.status_code == 429
    assert first.headers.get("retry-after") == "12"
    calls = provider.calls
    assert client.get("/api/analysis/themes").status_code == 429
    assert client.get("/api/analysis/differences").status_code == 429
    assert provider.calls == calls
