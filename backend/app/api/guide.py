from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_context
from app.api.schemas import (
    CoverageOut,
    GuideAnalyzeRequest,
    GuideOut,
    GuideQuestionOut,
    GuideQuestionResultOut,
    GuideReportOut,
    evidence_out,
)
from app.api.state import AppContext
from app.llm.errors import LLMError
from app.llm.extractive import ExtractiveLLMProvider
from app.services.guide_service import analyze_guide, analyze_guide_question

router = APIRouter()


@router.get("/guide", response_model=GuideOut)
def get_guide(context: AppContext = Depends(get_context)) -> GuideOut:
    return GuideOut(
        title=context.guide.title,
        objective=context.guide.objective,
        questions=[
            GuideQuestionOut(number=item.number, text=item.text)
            for item in context.guide.questions
        ],
    )


@router.post("/analysis/guide", response_model=GuideReportOut)
def analyze_interview_guide(
    body: GuideAnalyzeRequest = GuideAnalyzeRequest(),
    context: AppContext = Depends(get_context),
) -> GuideReportOut:
    request = body
    key = f"guide:{request.question_number or 'all'}"
    return context.request_gate.run(key, lambda: _analyze_guide(request, context))


def _analyze_guide(request: GuideAnalyzeRequest, context: AppContext) -> GuideReportOut:
    if request.question_number is None and context.guide_report is not None:
        return _report_out(context.guide_report)
    try:
        return _analyze_guide_with(request, context, context.provider)
    except LLMError:
        return _analyze_guide_with(request, context, ExtractiveLLMProvider())


def _analyze_guide_with(
    request: GuideAnalyzeRequest,
    context: AppContext,
    provider,
) -> GuideReportOut:
    if request.question_number is None:
        report = analyze_guide(
            context.guide,
            context.store,
            context.retriever,
            provider,
        )
        context.guide_report = report
        return _report_out(report)

    question = next(
        (item for item in context.guide.questions if item.number == request.question_number),
        None,
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Guide question not found.")
    result = analyze_guide_question(question, context.store, context.retriever, provider)
    return GuideReportOut(
        title=context.guide.title,
        objective=context.guide.objective,
        questions=[_question_out(result)],
    )


def _report_out(report) -> GuideReportOut:
    return GuideReportOut(
        title=report.title,
        objective=report.objective,
        questions=[_question_out(item) for item in report.questions],
    )


def _question_out(result) -> GuideQuestionResultOut:
    return GuideQuestionResultOut(
        number=result.question.number,
        question=result.question.text,
        answer=result.analysis.answer,
        evidence=[evidence_out(item) for item in result.analysis.evidence],
        coverage=[
            CoverageOut(
                expert=item.expert,
                market=item.market,
                evidence_ids=item.evidence_ids,
            )
            for item in result.coverage
        ],
        coverage_label=result.coverage_label,
        experts_covered=result.experts_covered,
        experts_total=result.experts_total,
    )
