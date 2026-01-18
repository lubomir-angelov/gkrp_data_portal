"""Application settings.

Settings are loaded from environment variables to support containerized
deployments.

No external configuration libraries are used.
"""

from __future__ import annotations

import os


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
