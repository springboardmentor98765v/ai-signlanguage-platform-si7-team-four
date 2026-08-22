"""Pre-deployment configuration validation.

Fails fast (before the app serves traffic) when running in production mode:

  - required environment variables are missing or empty,
  - a URL points at a dev-only / plain-HTTP endpoint in production.

Call ``validate_config_or_raise()`` from ``app/main.py`` before routers are
imported so a misconfigured deployment aborts cleanly at startup.
"""

import os

__all__ = ["validate_config", "validate_config_or_raise", "is_production"]

DEV_ENVS = {"development", "local", "test", ""}

PRODUCTION_REQUIRED_VARS = [
    "SECRET_KEY",
    "DATABASE_URL",
]


def is_production() -> bool:
    return os.getenv("APP_ENV", "").strip().lower() not in DEV_ENVS


def _reject_non_production_url(url: str, env_name: str) -> list[str]:
    """Return an error if `url` uses plain http:// in production."""
    if not url:
        return [f"missing or empty required env var: {env_name}"]
    if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
        return [f"{env_name} value '{url}' uses plain 'http://' in production (must use https://)."]
    return []


def validate_config() -> list[str]:
    """Return a list of configuration errors (empty when the config is safe)."""
    errors: list[str] = []

    if not is_production():
        return errors

    for var in PRODUCTION_REQUIRED_VARS:
        if not (os.getenv(var) or "").strip():
            errors.append(f"missing or empty required env var: {var}")

    for var in ("AI_SERVICE_URL", "FRONTEND_URL"):
        url = (os.getenv(var) or "").strip()
        if url:
            errors.extend(_reject_non_production_url(url, var))

    origins = (os.getenv("ALLOWED_ORIGINS") or "").strip()
    if not origins or origins == "*":
        errors.append(
            "ALLOWED_ORIGINS must be an explicit comma-separated list of origins "
            "in production; wildcard '*' is not allowed."
        )

    return errors


def validate_config_or_raise() -> None:
    """Raise ``SystemExit`` if the configuration is not production-safe."""
    errors = validate_config()
    if errors:
        formatted = "\n  - ".join(errors)
        raise SystemExit(
            f"FATAL: backend configuration check failed for APP_ENV={os.getenv('APP_ENV', '')!r}:\n"
            f"  - {formatted}\n"
            f"Fix Backend/.env or the deployment environment and restart the service."
        )