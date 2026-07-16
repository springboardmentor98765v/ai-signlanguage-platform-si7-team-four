from typing import Dict, List

SCORE_THRESHOLD: float = 70.0
ATTEMPT_WINDOW: int = 3


def group_scores_by_sign(attempts: List[dict]) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = {}
    for attempt in attempts:
        sign = attempt["sign"]
        score = attempt["score"]
        grouped.setdefault(sign, []).append(score)
    return grouped


def get_last_n_scores(scores: List[float], n: int = ATTEMPT_WINDOW) -> List[float]:
    return scores[-n:]


def needs_extra_practice(scores: List[float]) -> bool:
    last_scores = get_last_n_scores(scores)
    if len(last_scores) < ATTEMPT_WINDOW:
        return False
    average_score = sum(last_scores) / len(last_scores)
    return average_score < SCORE_THRESHOLD


def generate_recommendations(attempts: List[dict]) -> List[dict]:
    grouped_scores = group_scores_by_sign(attempts)
    recommendations: List[dict] = []

    for sign, scores in grouped_scores.items():
        if needs_extra_practice(scores):
            recommendations.append({
                "sign": sign,
                "message": f"Extra practice recommended for '{sign}'."
            })

    return recommendations