def is_match(predicted_sign: str, expected_sign: str) -> bool:
    return predicted_sign.strip().lower() == expected_sign.strip().lower()


def calculate_weighted_score(
    hand_shape_score: float,
    finger_position_score: float,
    timing_score: float,
    confidence: float,
) -> float:

    scores = [
        hand_shape_score,
        finger_position_score,
        timing_score,
        confidence,
    ]

    for score in scores:
        if not (0.0 <= score <= 1.0):
            raise ValueError("All scores must be between 0.0 and 1.0")

    overall_score = (
        (hand_shape_score * 0.40)
        + (finger_position_score * 0.25)
        + (timing_score * 0.15)
        + (confidence * 0.20)
    )

    return round(overall_score * 100, 2)


def assess(
    predicted_sign: str,
    expected_sign: str,
    confidence: float,
    hand_shape_score: float,
    finger_position_score: float,
    timing_score: float,
) -> dict:

    correct = is_match(predicted_sign, expected_sign)

    overall_accuracy = calculate_weighted_score(
        hand_shape_score,
        finger_position_score,
        timing_score,
        confidence,
    )

    return {
        "predicted_sign": predicted_sign,
        "expected_sign": expected_sign,
        "confidence": confidence,
        "hand_shape_score": hand_shape_score,
        "finger_position_score": finger_position_score,
        "timing_score": timing_score,
        "is_correct": correct,
        "overall_accuracy": overall_accuracy,
    }