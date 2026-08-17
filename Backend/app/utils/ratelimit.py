"""
Per-user (email-keyed) rate limiting for sensitive endpoints.

Uses the free, open-source `slowapi` library on top of `limits`.
The key function extracts the `email` field from the JSON request body so the
limit applies per account (per-user) rather than per IP. This prevents shared-IP
users (e.g. the same office Wi-Fi) from being wrongly blocked, while genuine
rapid abuse targeting a single account is still throttled. Requests without a
parseable email fall back to the client IP.
"""

import json

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

# Number of allowed attempts per window (per account).
# SRS requires per-user limiting on login; 5 attempts / minute is the policy.
LOGIN_LIMIT = "5/minute"
REGISTER_LIMIT = "5/minute"
PASSWORD_RESET_LIMIT = "5/minute"

LOGIN_ERROR_MESSAGE = (
    "Too many login attempts for this account. Please wait a minute and try again."
)
REGISTER_ERROR_MESSAGE = (
    "Too many registration attempts for this account. Please wait a minute and try again."
)
PASSWORD_RESET_ERROR_MESSAGE = (
    "Too many password reset requests for this account. Please wait a minute and try again."
)


def _email_key(request: Request) -> str:
    """
    Rate-limit key: lowercased email from the JSON request body when present,
    otherwise fall back to the client IP address.
    """
    body = getattr(request, "_body", None)
    email = ""
    if body:
        try:
            data = json.loads(body.decode("utf-8"))
            email = str(data.get("email") or "").strip().lower()
        except (ValueError, AttributeError, UnicodeDecodeError):
            email = ""

    if email:
        return f"user:{email}"

    return get_remote_address(request)


# Process-wide in-memory limiter (memory:// backend). Acceptable for the
# SQLite/local-dev backend; swap to Redis via RATELIMIT_STORAGE_URL in prod.
limiter = Limiter(
    key_func=_email_key,
    headers_enabled=True,
)
