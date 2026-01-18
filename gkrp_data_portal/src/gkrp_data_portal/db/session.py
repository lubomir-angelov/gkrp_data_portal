"""Database engine and session management."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from gkrp_data_portal.core.settings import get_database_url

logger = logging.getLogger(__name__)


def create_engine_from_env() -> Engine:
    """Create a SQLAlchemy engine from environment settings."""
    database_url = get_database_url()  # should raise if missing
    logger.info("Creating database engine")
    return create_engine(database_url, pool_pre_ping=True, future=True)


ENGINE: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def init_db() -> None:
    """Initialize database engine and session factory."""
    global ENGINE, SessionLocal  # noqa: PLW0603
    if ENGINE is not None and SessionLocal is not None:
        return
    ENGINE = create_engine_from_env()
    SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Yield a database session (FastAPI dependency style)."""
    if SessionLocal is None:
        init_db()
    assert SessionLocal is not None
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for non-FastAPI usage (NiceGUI pages, scripts)."""
    if SessionLocal is None:
        init_db()
    assert SessionLocal is not None
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
