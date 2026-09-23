"""Process-wide analysis context.

Architectural decision:
- One in-memory corpus is loaded at startup from the case files.
  Three transcripts do not need a database.
- Theme reports are built from the evidence store with the extractive
  provider. Groq is reserved for Ask/guide so a rate limit cannot blank
  the dashboard. Reports stay cached until re-ingest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import threading

from app.core.config import Settings, load_settings
from app.core.dedup import ExclusiveRequestGate
from app.llm.client import LLMProvider, OpenAIProvider
from app.llm.extractive import ExtractiveLLMProvider
from app.models.guide import InterviewGuide
from app.models.reports import GuideReport, ThemeReport
from app.models.transcript import Transcript
from app.services.evidence_store import EvidenceStore
from app.services.guide_parser import parse_guide_file
from app.services.ingestion import ingest_transcript
from app.services.retrieval import LexicalRetriever
from app.services.theme_service import analyze_themes


@dataclass
class AppContext:
    settings: Settings
    store: EvidenceStore
    transcripts: dict[str, Transcript]
    guide: InterviewGuide
    provider: LLMProvider
    retriever: LexicalRetriever
    request_gate: ExclusiveRequestGate = field(default_factory=ExclusiveRequestGate)
    theme_report: ThemeReport | None = None
    guide_report: GuideReport | None = None
    data_dir: Path = field(init=False, default=Path("."))
    _theme_lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self.data_dir = self.settings.data_dir

    def ingest(self) -> None:
        self.store.clear()
        self.transcripts.clear()
        for path in sorted(self.data_dir.glob("Transcript_*.txt")):
            transcript = ingest_transcript(path, self.store)
            self.transcripts[transcript.transcript_id] = transcript
        self.guide = parse_guide_file(self.data_dir / "Interview_Guide.txt")
        self.retriever = LexicalRetriever(self.store)
        self.theme_report = None
        self.guide_report = None

    def get_theme_report(self) -> ThemeReport:
        with self._theme_lock:
            if self.theme_report is None:
                self.theme_report = analyze_themes(self.store, ExtractiveLLMProvider())
            return self.theme_report


def create_runtime_provider(settings: Settings) -> LLMProvider:
    settings.require_groq_key()
    if settings.llm_provider == "groq":
        from app.llm.groq import GroqLLMClient

        return GroqLLMClient(settings)
    if settings.llm_provider == "openai" and settings.llm_api_key:
        return OpenAIProvider(settings)
    return ExtractiveLLMProvider()


def build_context(
    settings: Settings | None = None,
    provider: LLMProvider | None = None,
) -> AppContext:
    resolved = settings or load_settings()
    store = EvidenceStore()
    context = AppContext(
        settings=resolved,
        store=store,
        transcripts={},
        guide=parse_guide_file(resolved.data_dir / "Interview_Guide.txt"),
        provider=provider or create_runtime_provider(resolved),
        retriever=LexicalRetriever(store),
    )
    context.ingest()
    return context
