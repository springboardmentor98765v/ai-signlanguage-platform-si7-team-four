from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.feedback_service import generate_feedback

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)


class AssessmentResultRequest(BaseModel):
    scores: Dict[str, float]
    is_correct: bool = False


class FeedbackResponse(BaseModel):
    status: str
    flagged_categories: List[str]
    suggestions: List[str]


@router.post("", response_model=FeedbackResponse)
def get_feedback(request: AssessmentResultRequest):

    if not request.scores:
        raise HTTPException(
            status_code=400,
            detail="scores cannot be empty"
        )

    result = generate_feedback(
        assessment_result=request.scores,
        is_correct=request.is_correct,
    )

    return FeedbackResponse(**result)