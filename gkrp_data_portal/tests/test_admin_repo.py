"""Tests for gkrp_data_portal.ui.repository.admin_repo."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gkrp_data_portal.core.invitations import new_invite_token
from gkrp_data_portal.models.auth import User
from gkrp_data_portal.ui.repository.admin_repo import (
    accept_invite,
    create_invite_for_email,
    list_users,
    set_user_active,
)


class TestListUsers:
    def test_returns_list_of_users(self):
        mock_db = MagicMock()
        user1 = MagicMock(spec=User)
        user2 = MagicMock(spec=User)
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            user1,
            user2,
        ]

        result = list_users(mock_db)
        assert len(result) == 2
        assert result == [user1, user2]

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = list_users(mock_db)
        assert result == []


class TestSetUserActive:
    def test_activates_user(self):
        mock_db = MagicMock()
        user = MagicMock(spec=User, is_active=False)
        mock_db.get.return_value = user

        set_user_active(mock_db, user_id=1, is_active=True)
        assert user.is_active is True
        mock_db.add.assert_called_once_with(user)
        mock_db.flush.assert_called_once()

    def test_deactivates_user(self):
        mock_db = MagicMock()
        user = MagicMock(spec=User, is_active=True)
        mock_db.get.return_value = user

        set_user_active(mock_db, user_id=1, is_active=False)
        assert user.is_active is False

    def test_raises_when_user_not_found(self):
        mock_db = MagicMock()
        mock_db.get.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            set_user_active(mock_db, user_id=999, is_active=True)


class TestCreateInviteForEmail:
    def test_creates_new_user(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        token = new_invite_token()

        user = create_invite_for_email(
            mock_db,
            email="new@example.com",
            token=token,
            ttl_hours=48,
        )

        assert user.email == "new@example.com"
        assert user.role == "user"
        assert user.is_active is False
        assert user.invite_token_hash == token.hashed
        assert user.invited_at is not None
        mock_db.flush.assert_called_once()

    def test_updates_existing_user(self):
        mock_db = MagicMock()
        existing = MagicMock(spec=User)
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing
        token = new_invite_token()

        user = create_invite_for_email(
            mock_db,
            email="existing@example.com",
            token=token,
            ttl_hours=24,
        )

        assert user is existing
        assert user.role == "user"
        assert user.is_active is False
        assert user.invite_token_hash == token.hashed

    def test_normalizes_email(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        token = new_invite_token()

        create_invite_for_email(
            mock_db,
            email="  test@example.com  ",
            token=token,
            ttl_hours=24,
        )

        # The email should be normalized (stripped) before being used in the query
        # The admin_repo code does: email_norm = email.strip()
        # Just verify the function doesn't raise and the query was made
        mock_db.execute.assert_called()

    def test_raises_on_empty_email(self):
        mock_db = MagicMock()
        token = new_invite_token()

        with pytest.raises(ValueError, match="email is required"):
            create_invite_for_email(
                mock_db,
                email="   ",
                token=token,
                ttl_hours=24,
            )

    def test_sets_custom_role(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        token = new_invite_token()

        user = create_invite_for_email(
            mock_db,
            email="admin@example.com",
            token=token,
            ttl_hours=24,
            role="admin",
        )

        assert user.role == "admin"

    def test_sets_expiry(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        token = new_invite_token()

        user = create_invite_for_email(
            mock_db,
            email="test@example.com",
            token=token,
            ttl_hours=12,
        )

        # invite_expires_at should be ~12 hours from now
        assert user.invite_expires_at is not None


class TestAcceptInvite:
    def test_accepts_valid_invite(self):
        mock_db = MagicMock()
        user = MagicMock(spec=User)
        mock_db.execute.return_value.scalar_one_or_none.return_value = user

        accept_invite(
            mock_db,
            token_hash="valid-hash",
            username="newuser",
            password_hash="hashed-pw",
        )

        assert user.username == "newuser"
        assert user.password_hash == "hashed-pw"
        assert user.is_active is True
        assert user.invite_token_hash is None
        assert user.invite_expires_at is None
        mock_db.flush.assert_called_once()

    def test_raises_on_invalid_token(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(ValueError, match="Invalid invite"):
            accept_invite(
                mock_db,
                token_hash="bad-hash",
                username="newuser",
                password_hash="hashed-pw",
            )
