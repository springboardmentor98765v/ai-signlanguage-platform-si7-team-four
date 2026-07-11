from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.feedback_service import generate_feedback

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"]
)


class AssessmentResultRequest(BaseModel):
    scores: Dict[str, float]


class FeedbackResponse(BaseModel):
    flagged_categories: list
    suggestions: list


@router.post("", response_model=FeedbackResponse)
def get_feedback(request: AssessmentResultRequest):
    if not request.scores:
        raise HTTPException(
            status_code=400,
            detail="scores cannot be empty"
        )

    result = generate_feedback(request.scores)
    return FeedbackResponse(**result)