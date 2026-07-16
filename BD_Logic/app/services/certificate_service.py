"""
certificate_service.py

Business logic for certificate eligibility (Milestone 2, Day 6).

Scope (per SRS Milestone 2 / FR-4 / Cross-Domain Dependency Matrix):
- Defines certificate eligibility rules.
- Provides a pure eligibility-check function.
- Does NOT generate PDFs (later milestone).
- Does NOT connect to the database (Intern 5 scope).
- Does NOT use any AI-generated outputs.
- Kept independent of routing/transport concerns so it can be reused
  once database-backed learner records are wired in.
"""

from typing import NamedTuple

# --- Eligibility rule constants -------------------------------------------
# Centralized here so thresholds can be tuned without touching the
# eligibility logic itself.
MINIMUM_AVERAGE_SCORE: float = 80.0


class LearnerProgress(NamedTuple):
    """
    Minimal, transport-agnostic representation of the learner data
    required to evaluate certificate eligibility.

    This mirrors the shape expected from the future database-backed
    learner record (Intern 5 integration) so this service can be
    swapped over with minimal changes.
    """
    average_score: float
    all_required_letters_practiced: bool


def check_certificate_eligibility(progress: LearnerProgress) -> dict:
    """
    Evaluate certificate eligibility for a single learner.

    Eligibility rules (per FR-4):
    - average_score >= 80
    - all_required_letters_practiced == True

    Args:
        progress: LearnerProgress containing the learner's average score
                  and whether all required letters have been practiced.

    Returns:
        dict: {
            "eligible": bool,
            "message": str
        }
    """
    score_ok = progress.average_score >= MINIMUM_AVERAGE_SCORE
    letters_ok = progress.all_required_letters_practiced

    if score_ok and letters_ok:
        return {
            "eligible": True,
            "message": "Learner meets all requirements for certificate eligibility.",
        }

    reasons = []
    if not score_ok:
        reasons.append(
            f"average score {progress.average_score} is below the required "
            f"{MINIMUM_AVERAGE_SCORE}"
        )
    if not letters_ok:
        reasons.append("not all required letters have been practiced")

    return {
        "eligible": False,
        "message": "Learner is not eligible: " + "; ".join(reasons) + ".",
    }