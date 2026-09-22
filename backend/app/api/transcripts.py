from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_context
from app.api.schemas import (
    CorpusOut,
    IngestOut,
    SegmentOut,
    TranscriptDetailOut,
    TranscriptSummaryOut,
)
from app.api.state import AppContext
from app.models.resolution import TIMESTAMP_UNAVAILABLE

router = APIRouter()


def _summary(context: AppContext, transcript_id: str) -> TranscriptSummaryOut:
    transcript = context.transcripts[transcript_id]
    return TranscriptSummaryOut(
        transcript_id=transcript.transcript_id,
        expert=transcript.expert,
        role=transcript.role,
        market=transcript.market,
        segment_count=len(transcript.segments),
        evidence_count=len(context.store.list_by_transcript(transcript_id)),
    )


@router.get("/health", response_model=CorpusOut)
def corpus_status(context: AppContext = Depends(get_context)) -> CorpusOut:
    summaries = [_summary(context, transcript_id) for transcript_id in context.transcripts]
    return CorpusOut(
        expert_count=len({item.expert for item in context.store.list_all()}),
        evidence_count=len(context.store),
        transcript_count=len(context.transcripts),
        guide_question_count=len(context.guide.questions),
        provider=context.provider.model_name,
        transcripts=summaries,
    )


@router.post("/transcripts/ingest", response_model=IngestOut)
def ingest_transcripts(context: AppContext = Depends(get_context)) -> IngestOut:
    context.ingest()
    return IngestOut(
        transcript_count=len(context.transcripts),
        evidence_count=len(context.store),
        experts=sorted({item.expert for item in context.store.list_all()}),
    )


@router.get("/transcripts", response_model=list[TranscriptSummaryOut])
def list_transcripts(context: AppContext = Depends(get_context)) -> list[TranscriptSummaryOut]:
    return [_summary(context, transcript_id) for transcript_id in context.transcripts]


@router.get("/transcripts/{transcript_id}", response_model=TranscriptDetailOut)
def get_transcript(
    transcript_id: str,
    context: AppContext = Depends(get_context),
) -> TranscriptDetailOut:
    transcript = context.transcripts.get(transcript_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found.")
    summary = _summary(context, transcript_id)
    segments = [
        SegmentOut(
            segment_id=segment.segment_id,
            speaker=segment.speaker,
            timestamp=segment.timestamp,
            timestamp_display=segment.timestamp or TIMESTAMP_UNAVAILABLE,
            text=segment.text,
        )
        for segment in transcript.segments
    ]
    return TranscriptDetailOut(**summary.model_dump(), segments=segments)
