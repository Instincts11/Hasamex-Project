import os
from pathlib import Path

import pytest

os.environ["HASAMEX_SKIP_DOTENV"] = "1"
os.environ["HASAMEX_LLM_PROVIDER"] = "mock"

from app.services.evidence_store import EvidenceStore
from app.services.ingestion import ingest_transcript
from app.services.retrieval import LexicalRetriever

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

FRANCE_TRANSCRIPT = REPO_ROOT / "Transcript_1_France.txt"
GERMANY_TRANSCRIPT = REPO_ROOT / "Transcript_2_Germany.txt"
UK_TRANSCRIPT = REPO_ROOT / "Transcript_3_UK.txt"
INTERVIEW_GUIDE = REPO_ROOT / "Interview_Guide.txt"


@pytest.fixture(autouse=True)
def isolate_llm_environment(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    monkeypatch.setenv("HASAMEX_SKIP_DOTENV", "1")
    if request.node.get_closest_marker("groq_env") or request.node.get_closest_marker(
        "groq_integration"
    ):
        return
    monkeypatch.setenv("HASAMEX_LLM_PROVIDER", "mock")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.fixture
def france_path() -> Path:
    return FRANCE_TRANSCRIPT


@pytest.fixture
def germany_path() -> Path:
    return GERMANY_TRANSCRIPT


@pytest.fixture
def uk_path() -> Path:
    return UK_TRANSCRIPT


@pytest.fixture
def evidence_store(france_path: Path, germany_path: Path, uk_path: Path) -> EvidenceStore:
    store = EvidenceStore()
    ingest_transcript(france_path, store)
    ingest_transcript(germany_path, store)
    ingest_transcript(uk_path, store)
    return store


@pytest.fixture
def retriever(evidence_store: EvidenceStore) -> LexicalRetriever:
    return LexicalRetriever(evidence_store)


@pytest.fixture
def interview_guide_path() -> Path:
    return INTERVIEW_GUIDE
