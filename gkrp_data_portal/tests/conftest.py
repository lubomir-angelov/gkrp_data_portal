"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_db_session_state():
    """Reset module-level DB state before and after each test."""
    import gkrp_data_portal.db.session as session_mod

    original_engine = session_mod.ENGINE
    original_session = session_mod.SessionLocal

    session_mod.ENGINE = None
    session_mod.SessionLocal = None

    yield

    session_mod.ENGINE = original_engine
    session_mod.SessionLocal = original_session
