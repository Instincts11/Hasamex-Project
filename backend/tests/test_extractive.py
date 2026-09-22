import json

from app.llm.extractive import ExtractiveLLMProvider
from app.llm.prompts import build_qa_messages
from app.services.evidence_store import EvidenceStore
from app.services.retrieval import LexicalRetriever


def test_extractive_qa_keeps_one_best_quote_per_market(evidence_store: EvidenceStore) -> None:
    retriever = LexicalRetriever(evidence_store)
    hits = retriever.search("What are the purchase timelines?", top_k=10)
    assert len(hits) > 3
    provider = ExtractiveLLMProvider()
    completion = provider.complete(
        build_qa_messages("What are the purchase timelines?", hits)
    )
    payload = json.loads(completion.content)
    cited = payload["evidence_ids"]
    markets = [evidence_store.get(item_id).market for item_id in cited]
    assert len(cited) == len(set(markets))
    assert set(markets) == {"France", "Germany", "United Kingdom"}
    assert "ev_france_007" in cited
    assert "ev_germany_007" in cited
    assert "ev_united_kingdom_006" in cited
