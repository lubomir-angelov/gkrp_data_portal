"""Tests for gkrp_data_portal.auth.deps."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from gkrp_data_portal.auth.deps import (
    SESSION_USER_KEY,
    get_current_user,
    require_admin,
    require_user,
)


class TestGetCurrentUser:
    def test_returns_none_when_no_user_id(self):
        mock_db = MagicMock()
        with patch("gkrp_data_portal.auth.deps.app") as mock_app:
            mock_app.storage.user.get.return_value = None
            result = get_current_user(mock_db)
            assert result is None

    def test_returns_user_when_id_exists(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.get.return_value = mock_user

        with patch("gkrp_data_portal.auth.deps.app") as mock_app:
            mock_app.storage.user.get.return_value = "42"
            result = get_current_user(mock_db)
            assert result is mock_user
            mock_db.get.assert_called_once()
            call_args = mock_db.get.call_args
            assert call_args[0][1] == 42

    def test_converts_user_id_to_int(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.get.return_value = mock_user

        with patch("gkrp_data_portal.auth.deps.app") as mock_app:
            mock_app.storage.user.get.return_value = "123"
            get_current_user(mock_db)
            mock_db.get.assert_called_once()
            assert mock_db.get.call_args[0][1] == 123


class TestRequireUser:
    @contextmanager
    def _mock_session_scope(self, user):
        """Helper to mock session_scope as a context manager yielding a mock db."""
        with patch("gkrp_data_portal.auth.deps.session_scope") as mock_scope:
            mock_scope.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            with patch(
                "gkrp_data_portal.auth.deps.get_current_user", return_value=user
            ):
                yield

    def test_returns_user_when_authenticated(self):
        mock_user = MagicMock()
        mock_user.is_active = True
        with self._mock_session_scope(mock_user):
            result = require_user()
            assert result is mock_user

    def test_raises_when_not_authenticated(self):
        with self._mock_session_scope(None):
            with pytest.raises(
                PermissionError, match="Not authenticated or inactive user"
            ):
                require_user()

    def test_raises_when_inactive(self):
        mock_user = MagicMock()
        mock_user.is_active = False
        with self._mock_session_scope(mock_user):
            with pytest.raises(
                PermissionError, match="Not authenticated or inactive user"
            ):
                require_user()


class TestRequireAdmin:
    @contextmanager
    def _mock_session_scope(self, user):
        with patch("gkrp_data_portal.auth.deps.session_scope") as mock_scope:
            mock_scope.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            with patch(
                "gkrp_data_portal.auth.deps.get_current_user", return_value=user
            ):
                yield

    def test_returns_admin_user(self):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.role = "admin"
        with self._mock_session_scope(mock_user):
            result = require_admin()
            assert result is mock_user

    def test_raises_for_non_admin(self):
        mock_user = MagicMock()
        mock_user.is_active = True
        mock_user.role = "user"
        with self._mock_session_scope(mock_user):
            with pytest.raises(PermissionError, match="Admin privileges required"):
                require_admin()

    def test_raises_when_inactive(self):
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_user.role = "admin"
        with self._mock_session_scope(mock_user):
            with pytest.raises(
                PermissionError, match="Not authenticated or inactive user"
            ):
                require_admin()

    def test_raises_when_not_authenticated(self):
        with self._mock_session_scope(None):
            with pytest.raises(
                PermissionError, match="Not authenticated or inactive user"
            ):
                require_admin()


class TestSessionUserKey:
    def test_is_string(self):
        assert isinstance(SESSION_USER_KEY, str)

    def test_has_expected_name(self):
        assert SESSION_USER_KEY == "user_id"
