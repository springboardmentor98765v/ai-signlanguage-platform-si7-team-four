def is_match(predicted_sign: str, expected_sign: str) -> bool:
    return predicted_sign.strip().lower() == expected_sign.strip().lower()


def calculate_weighted_score(is_correct: bool, confidence: float) -> float:
    if not (0.0 <= confidence <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")

    return round(confidence, 4) if is_correct else 0.0


def assess(predicted_sign: str, expected_sign: str, confidence: float) -> dict:
    correct = is_match(predicted_sign, expected_sign)
    score = calculate_weighted_score(correct, confidence)

    return {
        "predicted_sign": predicted_sign,
        "expected_sign": expected_sign,
        "confidence": confidence,
        "is_correct": correct,
        "weighted_score": score,
    }