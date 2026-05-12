"""Tests for gkrp_data_portal.db.session."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import (
    create_engine_from_env,
    init_db,
    session_scope,
)


class TestCreateEngineFromEnv:
    def test_creates_engine(self):
        with patch(
            "gkrp_data_portal.db.session.get_database_url",
            return_value="sqlite:///:memory:",
        ):
            with patch("gkrp_data_portal.db.session.create_engine") as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine
                result = create_engine_from_env()
                assert result is mock_engine
                mock_create.assert_called_once_with(
                    "sqlite:///:memory:", pool_pre_ping=True, future=True
                )


class TestInitDb:
    def setUp(self):
        # Reset module-level state before each test
        import gkrp_data_portal.db.session as session_mod

        session_mod.ENGINE = None
        session_mod.SessionLocal = None

    def test_initializes_engine_and_session(self):
        import gkrp_data_portal.db.session as session_mod

        self.setUp()

        with patch(
            "gkrp_data_portal.db.session.get_database_url",
            return_value="sqlite:///:memory:",
        ):
            with patch("gkrp_data_portal.db.session.create_engine") as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine
                init_db()
                assert session_mod.ENGINE is mock_engine
                assert session_mod.SessionLocal is not None

    def test_does_not_reinitialize(self):
        self.setUp()

        with patch(
            "gkrp_data_portal.db.session.get_database_url",
            return_value="sqlite:///:memory:",
        ):
            with patch("gkrp_data_portal.db.session.create_engine") as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine
                init_db()
                init_db()
                assert mock_create.call_count == 1


class TestSessionScope:
    def test_yields_and_commits(self):
        with patch("gkrp_data_portal.db.session.SessionLocal") as mock_factory:
            mock_session = MagicMock(spec=Session)
            mock_factory.return_value = mock_session

            with session_scope() as db:
                assert db is mock_session

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_rolls_back_on_error(self):
        with patch("gkrp_data_portal.db.session.SessionLocal") as mock_factory:
            mock_session = MagicMock(spec=Session)
            mock_factory.return_value = mock_session

            with pytest.raises(RuntimeError):
                with session_scope():
                    raise RuntimeError("test error")

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_initializes_db_if_not_ready(self):
        import gkrp_data_portal.db.session as session_mod

        original_engine = session_mod.ENGINE
        original_session = session_mod.SessionLocal
        session_mod.ENGINE = None
        session_mod.SessionLocal = None

        try:
            with patch(
                "gkrp_data_portal.db.session.get_database_url",
                return_value="sqlite:///:memory:",
            ):
                with patch("gkrp_data_portal.db.session.create_engine"):
                    with patch(
                        "gkrp_data_portal.db.session.SessionLocal"
                    ) as mock_factory:
                        mock_session = MagicMock(spec=Session)
                        mock_factory.return_value = mock_session
                        with session_scope():
                            pass
                        mock_factory.assert_called()
        finally:
            session_mod.ENGINE = original_engine
            session_mod.SessionLocal = original_session
