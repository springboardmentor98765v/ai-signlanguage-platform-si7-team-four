"""
Milestone 3 - Day 5: Shared input-validation helpers (Intern 2)
----------------------------------------------------------------
Basic-but-effective checks applied consistently across routers/schemas:

  - reject_malicious(): blocks obvious XSS / SQL-injection patterns in free text.
  - Allowed-value sets for role, category, difficulty, notification event_type.

These are lightweight pattern checks (NOT a full WAF) per the SRS golden rule.
"""

import re

from fastapi import HTTPException, status

# ─────────────────────────────────────────────────────────
# Allowed-value sets (fixed contract)
# ─────────────────────────────────────────────────────────

ALLOWED_ROLES = {"Learner", "Instructor", "Accessibility Trainer", "Admin"}
ALLOWED_CATEGORIES = {"alphabet", "words", "numbers", "greetings", "phrases", "general"}
ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}
ALLOWED_NOTIFICATION_TYPES = {"info", "badge_earned", "certificate_ready", "new_recommendation"}

# ─────────────────────────────────────────────────────────
# Malicious-content detection (script tags / SQL-injection hints)
# ─────────────────────────────────────────────────────────

_MALICIOUS_PATTERNS = [
    # Script tags / event handlers / javascript: URLs
    r"<script\b",
    r"</script\b",
    r"<script[^>]*>",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
    r"onfocus\s*=",
    r"onmouseover\s*=",
    r"javascript\s*:",
    r"<iframe\b",
    r"<embed\b",
    r"<object\b",
    r"<svg\b",
    r"<img\b[^>]*onerror",
    # Obvious SQL-injection hints
    r"(\bunion\b\s*(\ball\b\s*)?\bselect\b)",
    r"(\bor\b\s+1\s*=\s*1\b)",
    r"(\bselect\b.*\bfrom\b.*\bwhere\b)",
    r"\binsert\s+into\b",
    r"\bdelete\s+from\b",
    r"\bdrop\s+table\b",
    r"\balter\s+table\b",
    r"(\bselect\s+load_file\b)",
    r"(\bupdate\s+\w+\s+set\b)",
    r"(--\s*)",
    r"(\'\s*\bor\s*\')",
    r"(\'\s*--)",
    r"(;\s*drop\b)",
    r"(;\s*delete\b)",
]

_MALICIOUS_REGEX = re.compile(
    "|".join(_MALICIOUS_PATTERNS),
    flags=re.IGNORECASE,
)


def has_malicious_content(value: str) -> bool:
    """
    Returns True if the string contains an obvious XSS or SQL-injection pattern.
    """
    if not value:
        return False
    return bool(_MALICIOUS_REGEX.search(value))


def reject_malicious(value):
    """
    Pydantic-compatible validator: raise ValueError (-> 422) on malicious input.
    """
    if has_malicious_content(value):
        raise ValueError("Input contains blocked script or SQL-injection patterns.")
    return value


def ensure_allowed(value: str, allowed: set, field_name: str) -> str:
    """
    Pydantic-compatible validator: raise ValueError unless value is in `allowed`.
    """
    if value not in allowed:
        raise ValueError(
            f"{field_name} must be one of: {sorted(allowed)} (got '{value}')."
        )
    return value


def reject_malicious_http(value: str) -> str:
    """
    Handler-level variant that raises HTTP 400 instead of Pydantic's 422.
    """
    if has_malicious_content(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input contains blocked script or SQL-injection patterns.",
        )
    return value
