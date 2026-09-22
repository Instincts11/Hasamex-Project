from fastapi import APIRouter, Depends

from app.api.deps import get_context
from app.api.schemas import AnswerOut, QARequest, evidence_out
from app.api.state import AppContext
from app.services.qa_service import answer_question

router = APIRouter()


@router.post("/qa", response_model=AnswerOut)
def ask_question(body: QARequest, context: AppContext = Depends(get_context)) -> AnswerOut:
    question = body.question.strip()
    result = context.request_gate.run(
        f"qa:{question.lower()}",
        lambda: answer_question(
            question,
            context.store,
            context.retriever,
            context.provider,
            top_k=context.settings.retrieval_top_k,
        ),
    )
    return AnswerOut(
        answer=result.answer,
        evidence=[evidence_out(item) for item in result.evidence],
    )
