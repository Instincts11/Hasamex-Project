"""Cross-transcript Q&A.

Architectural decision:
- One retrieval pass across the whole store, then the same grounding
  pipeline as the interview guide. Unsupported questions fail closed.
"""

from __future__ import annotations

from app.core.logging import log_pipeline
from app.llm.client import LLMProvider
from app.llm.prompts import build_qa_messages
from app.models.analysis import QAResponse
from app.models.resolution import ResolvedAnswer
from app.services.evidence_store import EvidenceStore
from app.services.grounding import generate_grounded_answer
from app.services.retrieval import LexicalRetriever


def answer_question(
    question: str,
    store: EvidenceStore,
    retriever: LexicalRetriever,
    provider: LLMProvider,
    *,
    top_k: int = 10,
) -> ResolvedAnswer:
    hits = retriever.search_scored(question, top_k=top_k)
    evidence = [hit.evidence for hit in hits]
    log_pipeline(
        "retrieval",
        question=question,
        retrieved_evidence_ids=[hit.evidence.evidence_id for hit in hits],
        retrieval_scores=[hit.score for hit in hits],
        top_k=top_k,
    )
    return generate_grounded_answer(
        provider,
        store,
        build_qa_messages(question, evidence),
        question=question,
        allowed_ids={item.evidence_id for item in evidence},
        retrieved_hits=hits,
        response_model=QAResponse,
    )
