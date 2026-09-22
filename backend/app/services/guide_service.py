"""Interview-guide analysis.

Architectural decision:
- Retrieval is per transcript so one loud market cannot hide the others.
- Synthesis goes through generate_grounded_answer. Quotes still come
  from the evidence store.
"""

from __future__ import annotations

from app.llm.client import LLMProvider
from app.llm.prompts import build_guide_messages
from app.models.analysis import AnalysisResponse
from app.models.guide import GuideQuestion, InterviewGuide
from app.models.reports import GuideQuestionResult, GuideReport
from app.services.coverage import coverage_from_citations, store_expert_total
from app.services.evidence_store import EvidenceStore
from app.services.grounding import generate_grounded_answer
from app.services.retrieval import LexicalRetriever, RetrievalFilters, RetrievalHit


def retrieve_per_transcript(
    retriever: LexicalRetriever,
    store: EvidenceStore,
    query: str,
    per_transcript_k: int = 4,
) -> list[RetrievalHit]:
    hits: list[RetrievalHit] = []
    seen: set[str] = set()
    transcript_ids = sorted({item.transcript_id for item in store.list_all()})
    for transcript_id in transcript_ids:
        for hit in retriever.search_scored(
            query,
            top_k=per_transcript_k,
            filters=RetrievalFilters(transcript_id=transcript_id),
        ):
            if hit.evidence.evidence_id in seen:
                continue
            seen.add(hit.evidence.evidence_id)
            hits.append(hit)
    return hits


def analyze_guide_question(
    question: GuideQuestion,
    store: EvidenceStore,
    retriever: LexicalRetriever,
    provider: LLMProvider,
    *,
    per_transcript_k: int = 4,
) -> GuideQuestionResult:
    hits = retrieve_per_transcript(retriever, store, question.text, per_transcript_k)
    evidence = [hit.evidence for hit in hits]
    analysis = generate_grounded_answer(
        provider,
        store,
        build_guide_messages(question.text, evidence),
        question=question.text,
        allowed_ids={item.evidence_id for item in evidence},
        retrieved_hits=hits,
        response_model=AnalysisResponse,
    )
    coverage, label, experts_covered, _single = coverage_from_citations(analysis.evidence, store)
    return GuideQuestionResult(
        question=question,
        analysis=analysis,
        coverage=coverage,
        coverage_label=label,
        experts_covered=experts_covered,
        experts_total=store_expert_total(store),
    )


def analyze_guide(
    guide: InterviewGuide,
    store: EvidenceStore,
    retriever: LexicalRetriever,
    provider: LLMProvider,
    *,
    per_transcript_k: int = 4,
) -> GuideReport:
    results = [
        analyze_guide_question(
            question,
            store,
            retriever,
            provider,
            per_transcript_k=per_transcript_k,
        )
        for question in guide.questions
    ]
    return GuideReport(title=guide.title, objective=guide.objective, questions=results)
