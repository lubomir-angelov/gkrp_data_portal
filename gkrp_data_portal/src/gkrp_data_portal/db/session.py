"""Database engine and session management."""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gkrp_data_portal.core.settings import get_database_url

logger = logging.getLogger(__name__)


def create_engine_from_env():
    """Create a SQLAlchemy engine from environment settings."""
    database_url = get_database_url()
    logger.info("Creating database engine")
    return create_engine(database_url, pool_pre_ping=True, future=True)


ENGINE = None
SessionLocal = None


def init_db() -> None:
    """Initialize database engine and session factory."""
    global ENGINE, SessionLocal  # noqa: PLW0603
    if ENGINE is not None:
        return
    ENGINE = create_engine_from_env()
    SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


def get_session():
    """Yield a database session (FastAPI dependency style)."""
    if SessionLocal is None:
        init_db()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
