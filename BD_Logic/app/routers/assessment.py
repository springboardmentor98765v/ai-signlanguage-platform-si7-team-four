from fastapi import APIRouter, HTTPException

from app.services import assessment_service

router = APIRouter(
    prefix="/assessment",
    tags=["assessment"]
)


@router.post("/evaluate")
def evaluate_assessment(predicted_sign: str, expected_sign: str, confidence: float):
    try:
        result = assessment_service.assess(
            predicted_sign,
            expected_sign,
            confidence
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result