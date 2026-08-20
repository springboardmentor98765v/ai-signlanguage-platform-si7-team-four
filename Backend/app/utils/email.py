"""Minimal email delivery helper used by the forgot-password flow.

Uses SMTP credentials from the environment (see Backend/.env.production.example):

    EMAIL_HOST / EMAIL_PORT / EMAIL_USERNAME / EMAIL_APP_PASSWORD / EMAIL_SENDER

If SMTP is not configured (local development), the message is written into
`Backend/mail_outbox/` and printed to the console so the flow remains
testable without live credentials.
"""

import os
import smtplib
import logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)

RESET_EMAIL_SUBJECT = "Reset your AI Sign Language Platform password"


def send_reset_password_email(recipient: str, reset_link: str) -> dict:
    """
    Deliver the password-reset message to `recipient`.

    Returns a small status dict describing which delivery path was used so the
    API response can inform the user accurately (real SMTP vs dev outbox).
    """
    smtp_host = os.getenv("EMAIL_HOST", "").strip()
    smtp_user = os.getenv("EMAIL_USERNAME", os.getenv("EMAIL_APP_PASSWORD_USER", "")).strip()
    sender = os.getenv("EMAIL_SENDER", smtp_user or "no-reply@signlanguage.local").strip()

    body = (
        "Hello,\n\n"
        "We received a request to reset the password for your AI Sign Language "
        "Platform account.\n\n"
        "Click the link below to choose a new password. The link expires in 30 minutes:\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email.\n\n"
        "— AI Sign Language Platform Team"
    )

    if smtp_host:
        try:
            msg = EmailMessage()
            msg["Subject"] = RESET_EMAIL_SUBJECT
            msg["From"] = sender
            msg["To"] = recipient
            msg.set_content(body)

            port = int(os.getenv("EMAIL_PORT", "587"))
            use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
            password = os.getenv("EMAIL_APP_PASSWORD", "")

            with smtplib.SMTP(smtp_host, port, timeout=15) as smtp:
                if use_tls:
                    smtp.starttls()
                if smtp_user and password:
                    smtp.login(smtp_user, password)
                smtp.send_message(msg)

            logger.info("Password-reset email sent to %s via SMTP %s", recipient, smtp_host)
            return {"sent": True, "method": "smtp"}
        except Exception as exc:  # pragma: no cover - depends on external SMTP
            logger.warning("SMTP delivery failed (%s); falling back to dev outbox.", exc)

    outbox_dir = os.path.join(os.path.dirname(__file__), "..", "..", "mail_outbox")
    os.makedirs(outbox_dir, exist_ok=True)
    outbox_path = os.path.join(outbox_dir, f"reset_{recipient.replace('@', '_at_')}.txt")
    with open(outbox_path, "w", encoding="utf-8") as fh:
        fh.write(f"TO: {recipient}\nSUBJECT: {RESET_EMAIL_SUBJECT}\n\n{body}\n")

    print("\n==============================================")
    print(" [PASSWORD RESET] (SMTP not configured - dev outbox)")
    print(f" To: {recipient}")
    print(f" Reset link: {reset_link}")
    print(" Written to: " + os.path.abspath(outbox_path))
    print("==============================================\n")

    return {"sent": True, "method": "outbox", "outbox_path": outbox_path}