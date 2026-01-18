"""Application settings.

Settings are loaded from environment variables to support containerized
deployments.

No external configuration libraries are used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def get_database_url() -> str:
    """Return the database URL.

    Environment variables:
        DATABASE_URL: SQLAlchemy database URL.

    Returns:
        A SQLAlchemy database URL.

    Raises:
        RuntimeError: If DATABASE_URL is not configured.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def get_secret_key() -> str:
    """Return the secret key used for signing tokens/cookies."""
    key = os.getenv("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY is not set")
    return key


def get_app_base_url() -> str:
    """Base URL used to construct invite links shown to admin."""
    return os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")


def get_invite_ttl_hours() -> int:
    v = os.getenv("INVITE_TTL_HOURS", "72")
    try:
        return max(1, int(v))
    except ValueError:
        return 72


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool


def get_smtp_settings() -> Optional[SmtpSettings]:
    """Return SMTP settings only if all required env vars are set."""
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM")

    if not all([host, port, username, password, sender]):
        return None

    try:
        port_i = int(port)
    except ValueError:
        return None

    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "y"}

    return SmtpSettings(
        host=host,
        port=port_i,
        username=username,
        password=password,
        sender=sender,
        use_tls=use_tls,
    )
