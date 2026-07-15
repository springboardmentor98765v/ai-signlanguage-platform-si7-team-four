from fastapi import APIRouter, HTTPException

from app.services import assessment_service

router = APIRouter(
    prefix="/assessment",
    tags=["assessment"]
)


@router.post("/evaluate")
def evaluate_assessment(
    predicted_sign: str,
    expected_sign: str,
    confidence: float,
    hand_shape_score: float,
    finger_position_score: float,
    timing_score: float,
):
    try:
        result = assessment_service.assess(
            predicted_sign=predicted_sign,
            expected_sign=expected_sign,
            confidence=confidence,
            hand_shape_score=hand_shape_score,
            finger_position_score=finger_position_score,
            timing_score=timing_score,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result