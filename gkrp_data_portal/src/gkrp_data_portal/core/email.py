from __future__ import annotations

import smtplib
from email.message import EmailMessage

from loguru import logger

from gkrp_data_portal.core.settings import get_smtp_settings


def maybe_send_invite_email(*, to_email: str, subject: str, body: str) -> bool:
    """Send email if SMTP is configured. Returns True if sent, False if skipped."""
    smtp = get_smtp_settings()
    if smtp is None:
        logger.info("SMTP not configured; skipping email send to {}", to_email)
        return False

    msg = EmailMessage()
    msg["From"] = smtp.sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        if smtp.use_tls:
            with smtplib.SMTP(smtp.host, smtp.port, timeout=20) as s:
                s.ehlo()
                s.starttls()
                s.ehlo()
                s.login(smtp.username, smtp.password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(smtp.host, smtp.port, timeout=20) as s:
                s.ehlo()
                s.login(smtp.username, smtp.password)
                s.send_message(msg)
        logger.info("Sent invite email to {}", to_email)
        return True
    except Exception:
        logger.exception("Failed to send invite email to {}", to_email)
        return False
