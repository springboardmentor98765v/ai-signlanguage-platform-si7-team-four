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
        "Try practicing with a slower tempo and a metronome to "
        "improve consistency between beats."
    ),
}

DEFAULT_SUGGESTION = "Review this area with your instructor for detailed guidance."


def _is_low_score(score: float) -> bool:
    return score <= LOW_SCORE_THRESHOLD


def generate_feedback(assessment_result: Dict[str, float]) -> Dict[str, List[str]]:
    if not assessment_result:
        return {
            "flagged_categories": [],
            "suggestions": []
        }

    flagged_categories: List[str] = []
    suggestions: List[str] = []

    for category, score in assessment_result.items():
        if _is_low_score(score):
            flagged_categories.append(category)
            suggestions.append(
                CORRECTION_RULES.get(category, DEFAULT_SUGGESTION)
            )

    return {
        "flagged_categories": flagged_categories,
        "suggestions": suggestions,
    }