from typing import Dict, List

LOW_SCORE_THRESHOLD = 60

CORRECTION_RULES: Dict[str, str] = {
    "thumb_position": (
        "Keep your thumb relaxed and aligned with the second finger; "
        "avoid collapsing the thumb joint inward."
    ),
    "finger_extension": (
        "Extend your fingers fully and evenly; avoid curling or "
        "stiffness at the fingertips."
    ),
    "timing": (
        "Hold the gesture slightly longer and practice with a slower tempo "
        "to improve timing consistency."
    ),
    "hand_shape": (
        "Maintain the correct hand shape throughout the gesture."
    ),
    "finger_position": (
        "Keep your fingers closer together and avoid unnecessary movement."
    ),
}

DEFAULT_SUGGESTION = (
    "Review this gesture again and practice slowly."
)


def _is_low_score(score: float) -> bool:
    return score <= LOW_SCORE_THRESHOLD


def generate_feedback(
    assessment_result: Dict[str, float],
    is_correct: bool = False,
) -> Dict[str, List[str] | str]:

    if not assessment_result:
        return {
            "status": "No assessment data.",
            "flagged_categories": [],
            "suggestions": [],
        }

    flagged_categories: List[str] = []
    suggestions: List[str] = []

    for category, score in assessment_result.items():

        if _is_low_score(score):

            flagged_categories.append(category)

            suggestions.append(
                CORRECTION_RULES.get(category, DEFAULT_SUGGESTION)
            )

    if is_correct:

        encouragement = (
            "Excellent! Your gesture was recognized correctly. "
            "Keep practicing to maintain consistency."
        )

    else:

        encouragement = (
            "Good attempt! Practice the highlighted areas and try again."
        )

    return {
        "status": encouragement,
        "flagged_categories": flagged_categories,
        "suggestions": suggestions,
    }