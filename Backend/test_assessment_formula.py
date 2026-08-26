"""
Section D / D1: Certification & Assessment scoring-formula unit tests.

Covers the live assessment weighting used by every practice session and the
certificate eligibility policy:

  - weighted score = hand_shape*0.40 + finger_position*0.25 + timing*0.15
                     + confidence*0.20, expressed on a 0-100 scale.
  - exact-match is case-insensitive.
  - out-of-range component scores are rejected.
  - certificate eligibility requires a >= 80% average and every required
    letter practiced (MINIMUM_AVERAGE_SCORE policy).
"""

import pytest

from app.services.assessment_service import (
    calculate_weighted_score,
    is_match,
    assess,
)
from app.services.certificate_service import (
    check_certificate_eligibility,
    LearnerProgress,
    MINIMUM_AVERAGE_SCORE,
)


def test_perfect_input_scores_100():
    score = calculate_weighted_score(1.0, 1.0, 1.0, 1.0)
    assert score == 100.0


def test_weights_produce_expected_mix():
    # Only hand_shape perfect at 1.0, everything else zero.
    assert calculate_weighted_score(1.0, 0.0, 0.0, 0.0) == pytest.approx(40.0)
    assert calculate_weighted_score(0.0, 1.0, 0.0, 0.0) == pytest.approx(25.0)
    assert calculate_weighted_score(0.0, 0.0, 1.0, 0.0) == pytest.approx(15.0)
    assert calculate_weighted_score(0.0, 0.0, 0.0, 1.0) == pytest.approx(20.0)


def test_typical_partial_scores():
    score = calculate_weighted_score(0.8, 0.6, 0.9, 0.7)
    expected = (0.8 * 0.40) + (0.6 * 0.25) + (0.9 * 0.15) + (0.7 * 0.20)
    assert score == pytest.approx(expected * 100, abs=0.01)


def test_out_of_range_component_rejected():
    with pytest.raises(ValueError):
        calculate_weighted_score(1.1, 0.5, 0.5, 0.5)
    with pytest.raises(ValueError):
        calculate_weighted_score(0.5, -0.1, 0.5, 0.5)


def test_is_match_is_case_insensitive_and_trimmed():
    assert is_match("a", "A")
    assert is_match(" THANK ", "thank")
    assert not is_match("a", "b")


def test_assess_correct_sign_and_accuracy_scale():
    result = assess(
        predicted_sign="A",
        expected_sign="a",
        confidence=0.9,
        hand_shape_score=0.9,
        finger_position_score=0.9,
        timing_score=0.9,
    )
    assert result["is_correct"] is True
    assert 0.0 <= result["overall_accuracy"] <= 100.0
    assert result["overall_accuracy"] == pytest.approx(
        (0.9 * 0.40 + 0.9 * 0.25 + 0.9 * 0.15 + 0.9 * 0.20) * 100,
        abs=0.01,
    )


def test_assess_incorrect_sign():
    result = assess(
        predicted_sign="B",
        expected_sign="A",
        confidence=0.9,
        hand_shape_score=0.9,
        finger_position_score=0.9,
        timing_score=0.9,
    )
    assert result["is_correct"] is False


def test_certificate_policy_threshold():
    assert MINIMUM_AVERAGE_SCORE == 80.0

    eligible = check_certificate_eligibility(
        LearnerProgress(average_score=85.0, all_required_letters_practiced=True)
    )
    assert eligible["eligible"] is True

    low_score = check_certificate_eligibility(
        LearnerProgress(average_score=79.9, all_required_letters_practiced=True)
    )
    assert low_score["eligible"] is False
    assert "average score" in low_score["message"]

    missing_letters = check_certificate_eligibility(
        LearnerProgress(average_score=90.0, all_required_letters_practiced=False)
    )
    assert missing_letters["eligible"] is False
    assert "letters" in missing_letters["message"]