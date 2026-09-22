# Hasamex AI Engineer — Architecture & Build Specification

## 1. Product Definition

Build a **web-based AI expert-call analysis application**.

This is NOT just a chatbot. It is an AI research/analysis dashboard with:
1. Interview-guide question analysis
2. Exact source quotes
3. Source timestamps
4. Cross-expert common themes
5. Cross-expert disagreements/differences
6. Conversational Q&A across all transcripts
7. Evidence-grounded answers with traceable provenance

The application must use the supplied 3 expert transcripts as the source of truth.

Core principle:

> The LLM interprets evidence; it does not create evidence.

Never invent quotes, timestamps, experts, markets, facts, or conclusions unsupported by the transcripts.

---

# 2. Actual Case Data

## Expert 1
Name: Dr. Jean Martin
Role: Head of Urology
Market: France

Key transcript facts:
- 00:18: Adoption is growing, concentrated in larger academic hospitals and private centres with stronger capital budgets; smaller regional hospitals are slower.
- 01:20: Biggest issue is capital budget approval.
- 02:18: ROI is very important; finance considers utilisation, procedure volume, maintenance cost, and whether the system pays for itself.
- 03:10: Training matters; several surgeons need training so utilisation is high enough.
- 04:08: Clinical outcomes are necessary but not sufficient; economics and utilisation matter when outcomes are similar.
- 05:07: Expects steady rather than explosive growth; maybe 15–20% more procedures annually in some stronger centres; smaller hospitals slower.
- 06:08: Purchase decision realistically takes 6–12 months, potentially longer if pushed into a new budget cycle.

## Expert 2
Name: Anna Keller
Role: Former Hospital Procurement Director
Market: Germany

Key transcript facts:
- 00:16: Adoption is growing but uneven; large university hospitals are more advanced while smaller hospitals are waiting.
- 01:10: Cost is first barrier; hospital finances are under pressure; second issue is proving sufficient use.
- 02:08: Procurement focuses on total cost of ownership, procedure volume, maintenance, service contracts and training; clinical case helps, economic case decides approval.
- 03:05: Training is operationally important; if only one surgeon is comfortable, utilisation is poor and business case weakens.
- 04:09: Expects gradual rather than dramatic growth because hospitals have competing capital priorities.
- 05:08: Expects high single-digit or low double-digit procedure-volume growth rather than 20% across the whole market.
- 06:05: Purchase process commonly takes 9–18 months because procurement, clinical leadership, finance and management need alignment.

## Expert 3
Name: Dr. Emily Carter
Role: Consultant Urologist
Market: United Kingdom

Key transcript facts:
- 00:14: Adoption is increasing; in some larger NHS trusts robotic surgery is becoming standard for selected procedures; access varies by hospital.
- 01:05: Funding matters, but training capacity is just as important.
- 02:07: ROI matters, but hospitals also consider patient outcomes, length of stay, surgeon recruitment and clinical position.
- 03:10: Economics and clinical strategy are balanced; finance alone does not decide purchase.
- 04:06: Positive outlook; adoption could accelerate if training expands and systems become more cost competitive; above 15% annual procedure growth in some areas.
- 05:04: 6–9 months can happen if funding is already available; much longer if waiting for a new capital cycle.
- 06:04: Adoption is not just buying the machine; enough trained people and enough procedure volume are needed for sustainability.

---

# 3. Product Architecture

Use this architecture:

```text
                    HASAMEX AI ANALYZER
                           |
                     WEB APPLICATION
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
  INTERVIEW GUIDE    THEMES & DIFFERENCES   CROSS-CALL Q&A
        |                  |                  |
        +------------------+------------------+
                           |
                           v
                    FASTAPI BACKEND
                           |
            +--------------+--------------+
            |              |              |
            v              v              v
        RETRIEVAL         LLM        VALIDATION
            |              |              |
            +--------------+--------------+
                           |
                           v
                    EVIDENCE LAYER
                           |
                 +---------+---------+
                 |         |         |
                 v         v         v
              Quote   Timestamp   Provenance
                           |
                           v
                      NEXT.JS UI
```

---

# 4. Core Data Flow

The canonical pipeline is:

```text
SOURCE
  ↓
PARSE
  ↓
NORMALIZE
  ↓
CREATE EVIDENCE IDs
  ↓
STORE EVIDENCE
  ↓
RETRIEVE RELEVANT EVIDENCE
  ↓
LLM REASONING
  ↓
STRUCTURED OUTPUT
  ↓
VALIDATE
  ↓
RESOLVE EVIDENCE IDs
  ↓
DISPLAY ANSWER + EXACT QUOTE + TIMESTAMP
```

Keep this separation strict.

## Deterministic code should handle:
- Parsing
- Timestamp extraction
- Speaker extraction
- Expert metadata
- Market metadata
- Evidence IDs
- Chunk IDs
- Retrieval
- Evidence lookup
- Quote/source resolution
- Pydantic validation
- Error handling
- Deduplication

## LLM should handle:
- Answer synthesis
- Semantic interpretation
- Theme identification
- Claim normalization
- Disagreement interpretation
- Natural-language response generation

---

# 5. Evidence-First Design

Create an immutable evidence object:

```python
class Evidence(BaseModel):
    evidence_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    speaker: str
    timestamp: str | None
    text: str
```

The LLM should return evidence IDs, NOT generated quotes or timestamps.

Example:

```json
{
  "answer": "Economic considerations are a major adoption barrier.",
  "evidence_ids": ["ev_001", "ev_014", "ev_031"]
}
```

The backend resolves:

```text
ev_001 → actual transcript text
ev_014 → actual transcript text
ev_031 → actual transcript text
```

Never trust model-generated source metadata.

This is a major anti-hallucination mechanism.

---

# 6. Data Models

Implement models similar to:

```python
class TranscriptSegment(BaseModel):
    segment_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    speaker: str
    timestamp: str | None
    text: str


class Evidence(BaseModel):
    evidence_id: str
    transcript_id: str
    expert: str
    role: str
    market: str
    speaker: str
    timestamp: str | None
    text: str


class AnalysisResponse(BaseModel):
    answer: str
    evidence_ids: list[str]


class Theme(BaseModel):
    name: str
    summary: str
    supporting_evidence_ids: list[str]
    conflicting_evidence_ids: list[str]


class Claim(BaseModel):
    topic: str
    claim: str
    scope: str | None = None
    evidence_ids: list[str]


class QAResponse(BaseModel):
    answer: str
    evidence_ids: list[str]
```

---

# 7. Three Main AI Workflows

## A. Interview Guide

```text
Interview question
       ↓
Retrieve relevant evidence from each transcript
       ↓
LLM
       ↓
Structured answer + evidence IDs
       ↓
Pydantic validation
       ↓
Evidence resolution
       ↓
Answer + exact quotes + timestamps
```

The UI should make it obvious which expert supports each statement.

---

## B. Themes and Disagreements

Do NOT directly ask the LLM to produce a vague summary.

Use:

```text
Transcripts
    ↓
Extract claims/observations
    ↓
Normalize semantically related claims
    ↓
Group into themes
    ↓
Compare expert positions
    ↓
Identify:
  - common themes
  - supporting evidence
  - differing emphasis
  - genuine contradictions
    ↓
Validate evidence
    ↓
Display
```

Important distinction:

- Same topic does NOT automatically mean consensus.
- Different wording does NOT automatically mean disagreement.
- A conditional statement is not necessarily a contradiction.
- Preserve expert-specific scope.

Example:

France says 15–20% growth in some stronger centres.
Germany says high single digits/low double digits rather than 20% across the whole market.
UK says above 15% in some areas.

Do NOT summarize this as "the market will grow 15–20%."

Preserve scope.

---

## C. Cross-Transcript Q&A

```text
User question
      ↓
Retrieve relevant evidence across all 3 transcripts
      ↓
LLM
      ↓
Structured response
      ↓
Validate evidence IDs
      ↓
Resolve source evidence
      ↓
Answer + citations
```

If the corpus does not contain enough evidence:

```text
No supporting evidence was found in the provided transcripts.
```

Do not answer from the model's general world knowledge.

---

# 8. Important Edge Cases

Handle these explicitly:

### No evidence
Return a grounded no-evidence response.

### Missing timestamp
Never invent one. Display "Timestamp unavailable."

### Unknown evidence ID
Reject or retry invalid model output.

### Hallucinated quote
Never display a model-generated quote. Resolve quote from the original evidence store.

### Conflicting evidence
Preserve both positions.

### Single-expert theme
Label it as single-expert evidence rather than cross-expert consensus.

### Conditional forecasts
Preserve the condition and scope.

### Unsupported question
Say that the provided transcripts do not contain enough evidence.

### Prompt injection in transcript
Treat transcript content as untrusted data, never as system instructions.

### Duplicate evidence
Deduplicate before presenting.

---

# 9. Retrieval Strategy

The current corpus is tiny.

Do NOT overengineer.

For the assignment:
- Start with deterministic/simple lexical retrieval or lightweight semantic retrieval.
- Keep retrieval behind an interface.
- Do not require a heavyweight vector database for the first version.

Design:

```python
class Retriever(Protocol):
    def search(self, query: str, top_k: int = 8) -> list[Evidence]:
        ...
```

This allows future replacement with:

```text
Simple retrieval
      ↓
Hybrid BM25 + embeddings
      ↓
Reranking
      ↓
Top-k evidence
```

For 30+ transcripts, add:
- Persistent document/evidence storage
- Embeddings
- Vector index
- Hybrid retrieval
- Metadata filtering
- Reranking
- Async ingestion
- Batch embedding
- Caching
- Observability

---

# 10. UI

Build a clean analyst dashboard, not a generic ChatGPT clone.

Main navigation:

```text
Dashboard
Interview Guide
Themes & Differences
Ask the Transcripts
Transcript Explorer
```

## Dashboard

Show:
- 3 experts
- markets
- roles
- corpus status
- evidence count

## Interview Guide

For every guide question show:
- Answer
- Evidence coverage
- Expert/market
- Exact quote
- Timestamp
- Link/button to transcript context

## Themes & Differences

Show:
- Theme name
- Summary
- Coverage e.g. 3/3 experts
- Supporting evidence
- Differing positions
- Contradictory evidence if applicable

## Q&A

Chat-like interface:
- Question
- Grounded answer
- Source evidence cards
- Exact quotes
- Timestamps
- Expert/market

## Transcript Explorer

Show original transcript segments with timestamps and speakers.

---

# 11. Suggested Frontend

Use:

- Next.js
- TypeScript
- Tailwind CSS

Components:

```text
ExpertCard
GuideQuestionCard
EvidenceCard
ThemeCard
DifferenceCard
TranscriptViewer
CitationBadge
ChatPanel
```

Clicking a citation should open or scroll to the corresponding transcript evidence.

---

# 12. Suggested Backend

Use:

- Python
- FastAPI
- Pydantic
- LLM API
- Simple retrieval initially

Project structure:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── guide.py
│   │   ├── themes.py
│   │   └── qa.py
│   ├── models/
│   │   ├── transcript.py
│   │   ├── evidence.py
│   │   └── analysis.py
│   ├── services/
│   │   ├── parser.py
│   │   ├── ingestion.py
│   │   ├── retrieval.py
│   │   ├── guide_service.py
│   │   ├── theme_service.py
│   │   ├── qa_service.py
│   │   └── validation.py
│   ├── llm/
│   │   ├── client.py
│   │   └── prompts.py
│   └── core/
│       ├── config.py
│       └── logging.py
└── tests/
    ├── test_parser.py
    ├── test_retrieval.py
    ├── test_quotes.py
    ├── test_analysis.py
    └── test_api.py
```

---

# 13. API

Implement approximately:

```text
POST /api/transcripts/ingest
GET  /api/transcripts
GET  /api/transcripts/{id}

POST /api/analysis/guide
GET  /api/analysis/themes
GET  /api/analysis/differences

POST /api/qa
```

Q&A request:

```json
{
  "question": "What are the main barriers to adoption?"
}
```

Response:

```json
{
  "answer": "Economic considerations are a common barrier...",
  "evidence": [
    {
      "evidence_id": "ev_001",
      "expert": "Dr. Jean Martin",
      "market": "France",
      "timestamp": "01:20",
      "quote": "The biggest issue is still capital budget approval."
    }
  ]
}
```

---

# 14. Testing Strategy

Write tests for:

1. Timestamp parsing
2. Speaker parsing
3. Evidence ID generation
4. Retrieval relevance
5. Evidence ID validation
6. Exact quote resolution
7. Missing timestamp behavior
8. No-evidence behavior
9. Unsupported questions
10. Conflicting evidence
11. Scope preservation
12. Duplicate evidence

Example important test:

```text
Question:
"What is the average price of a robotic surgery system?"

Expected:
No supporting evidence found.
```

Another:

```text
Question:
"Do all experts say economics alone determines purchasing?"

Expected:
No.
The UK expert explicitly describes economics and clinical strategy
as balanced.
```

---

# 15. Evaluation

Create a small golden evaluation set.

Track:

- Retrieval precision
- Retrieval recall
- Citation accuracy
- Quote accuracy
- Groundedness
- Evidence coverage
- Completeness

Do not use meaningless "AI confidence = 95%" as the primary quality metric.

---

# 16. Observability

Log structured metadata:

```text
request_id
question
retrieved_evidence_ids
retrieval_scores
prompt_version
model
latency
token_usage
validation_result
final_evidence_ids
```

This lets us debug the complete AI pipeline.

---

# 17. Senior Engineering Principles

Follow these principles:

1. Source of truth is always the transcript.
2. LLM output is untrusted input.
3. Evidence metadata is deterministic.
4. Model returns evidence IDs, not source metadata.
5. Backend resolves quotes and timestamps.
6. Preserve uncertainty and disagreement.
7. Preserve scope and conditions.
8. Do not overengineer the 3-transcript version.
9. Make retrieval replaceable.
10. Separate deterministic processing from probabilistic reasoning.
11. Validate every structured model response.
12. Prefer "insufficient evidence" over hallucination.
13. Design for 30+ transcripts without changing the core analysis contracts.

---

# 18. Demo Story

The demo should show:

### Demo 1
Ask an interview-guide question.

Show:
Answer → evidence → exact quote → timestamp.

### Demo 2
Open Themes & Differences.

Show:
Economic constraints, training, utilisation, clinical strategy.

### Demo 3
Show a genuine difference:
France/Germany emphasize economics strongly, while the UK expert describes economics and clinical strategy as balanced.

### Demo 4
Ask:
"What are the purchase timelines?"

Show:
France 6–12 months
Germany 9–18 months
UK 6–9 months if funding is already available, potentially longer otherwise.

### Demo 5
Ask something unsupported:
"What is the average price of a robotic surgery system?"

Show:
"No supporting evidence was found in the provided transcripts."

This demonstrates groundedness.

---

# 19. Coding Instructions for Cursor

Build incrementally.

Do NOT generate the entire project blindly in one file.

First:
1. Create project structure.
2. Implement transcript models.
3. Implement parser.
4. Create evidence store.
5. Add parser tests.
6. Implement retrieval interface and simple retriever.
7. Add Pydantic analysis schemas.
8. Add LLM provider abstraction.
9. Implement guide analysis.
10. Implement validation/evidence resolution.
11. Implement themes/differences.
12. Implement Q&A.
13. Build FastAPI routes.
14. Build frontend.
15. Add tests.
16. Add README and local run instructions.

Keep functions small and testable.

Use type hints.

Use environment variables for API keys.

Never hardcode secrets.

Add clear error handling.

Do not invent transcript data.

Do not fabricate timestamps or quotes.

Do not add unnecessary infrastructure.

Before changing architecture, explain the reason in comments or README.

The final code should be understandable enough for a technical interviewer to inspect.

