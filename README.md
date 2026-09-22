# Hasamex AI Analyzer

Evidence-first analysis of three European robotic-surgery expert calls. This is an analyst dashboard, not a chatbot.

The transcripts are the only source of truth. The model may interpret evidence. It does not create quotes, timestamps, experts, markets, or facts.

## Architecture

```text
Transcript files
    → parse / ingest          (deterministic)
    → evidence store          (IDs, exact text, timestamps)
    → retrieval               (lexical, replaceable)
    → LLM JSON                (answer + evidence_ids only)
    → validate IDs            (must exist and have been retrieved)
    → resolve quotes          (always from the store)
    → FastAPI + Next.js UI
```

Deterministic code owns parsing, IDs, retrieval, validation, and quote resolution. The LLM returns evidence IDs, never source metadata.

Default synthesis (no API key) is an extractive provider that only cites IDs already in the prompt. Set `HASAMEX_LLM_PROVIDER=groq` and `GROQ_API_KEY` in `backend/.env` to use Groq. OpenAI remains available via `HASAMEX_LLM_PROVIDER=openai`. The trust boundary does not change: the model returns evidence IDs, and quotes are resolved from the store.

## Case data

| File | Expert | Market |
|---|---|---|
| `Transcript_1_France.txt` | Dr. Jean Martin, Head of Urology | France |
| `Transcript_2_Germany.txt` | Anna Keller, Former Hospital Procurement Director | Germany |
| `Transcript_3_UK.txt` | Dr. Emily Carter, Consultant Urologist | United Kingdom |

Do not invent transcript content. The parser reads these files verbatim.

## Local run

Use two terminals.

**API** (from `backend`):

```powershell
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**UI** (from `frontend`):

```powershell
npm install
npx next dev -p 3000
```

Open [http://localhost:3000](http://localhost:3000). The Next.js app proxies `/backend/*` to `http://127.0.0.1:8000/api/*`.

Optional Groq synthesis: copy `backend/.env.example` to `backend/.env` and set `HASAMEX_LLM_PROVIDER=groq` plus `GROQ_API_KEY`. Optional knobs: `GROQ_MODEL`, `GROQ_TIMEOUT_SECONDS`, `GROQ_MAX_CONCURRENT_REQUESTS`. Never put keys in source, frontend code, or logs. Tests run without a real key (`HASAMEX_GROQ_INTEGRATION=1` enables a live call). The default `mock` provider is extractive: one best quote per market, IDs only from retrieved evidence.

## Demo path

1. Dashboard — three experts, 21 evidence items.
2. Themes & Differences — growth scope and economics vs clinical strategy.
3. Ask the Transcripts — “What are the purchase timelines?”
4. Ask an unsupported question — “What is the average price of a robotic surgery system?”
5. Follow a citation into Transcript Explorer.

France 6–12 months, Germany 9–18 months, UK 6–9 months if funding is already available. The UK expert says economics and clinical strategy are balanced. No transcript states a system price.

## Tests

From `backend`:

```powershell
python -m pytest
```

## Golden evaluation

Metrics are evidence quality, not “AI confidence = 95%”:

- retrieval precision / recall
- citation accuracy
- quote accuracy (resolved text equals store text)
- groundedness (no invented sources; unsupported questions stay empty)
- evidence coverage (expected markets)
- completeness (required IDs and quote substrings)

```powershell
cd backend
python -m eval.run_eval
```

The golden set is `backend/eval/golden_set.json`.

## Observability

Each grounded call logs JSON with:

`request_id`, `question`, `retrieved_evidence_ids`, `retrieval_scores`, `prompt_version`, `model`, `latency_ms`, `token_usage`, `validation_result`, `final_evidence_ids`

Retrieval scores are ranks for debugging. They are not shown as confidence.

## How this scales from 3 transcripts to 30+

Keep the same contracts: `Evidence`, `Retriever.search`, `AnalysisResponse` / `QAResponse` (IDs only), store-backed resolution.

Replace the in-memory store and lexical retriever with persistent documents, embeddings, hybrid search, metadata filters, and reranking. Do not let the model start returning quotes or timestamps.

## Project layout

```text
backend/app/models/     transcript, evidence, analysis schemas
backend/app/services/   parser, store, retrieval, grounding, guide/themes/QA
backend/app/llm/        provider protocol, prompts, extractive fallback
backend/app/api/        FastAPI routes
backend/eval/           golden set and metrics
frontend/src/app/       Dashboard, Guide, Themes, Ask, Explorer
```

Ignore `task/`. It is not this application.
