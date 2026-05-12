"""Tests for gkrp_data_portal.core.invitations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from gkrp_data_portal.core.invitations import (
    InviteToken,
    compute_expiry,
    is_expired,
    new_invite_token,
    verify_token,
)


class TestNewInviteToken:
    def test_returns_invite_token(self):
        token = new_invite_token()
        assert isinstance(token, InviteToken)

    def test_raw_and_hashed_are_different(self):
        token = new_invite_token()
        assert token.raw != token.hashed

    def test_raw_is_url_safe(self):
        token = new_invite_token()
        # URL-safe base64 uses A-Z, a-z, 0-9, -, _
        assert all(c.isalnum() or c in "-_" for c in token.raw)

    def test_hashed_is_sha256_hex(self):
        token = new_invite_token()
        # SHA-256 hex digest is 64 chars of [0-9a-f]
        assert len(token.hashed) == 64
        assert all(c in "0123456789abcdef" for c in token.hashed)

    def test_each_call_produces_unique_token(self):
        tokens = {new_invite_token().raw for _ in range(100)}
        assert len(tokens) == 100


class TestVerifyToken:
    def test_verifies_correct_token(self):
        token = new_invite_token()
        assert verify_token(token.raw, token.hashed) is True

    def test_rejects_wrong_token(self):
        token = new_invite_token()
        assert verify_token("wrong-token", token.hashed) is False

    def test_rejects_none_hash(self):
        assert verify_token("any-token", None) is False

    def test_rejects_empty_hash(self):
        assert verify_token("any-token", "") is False


class TestIsExpired:
    def test_none_is_expired(self):
        assert is_expired(None) is True

    def test_future_datetime_not_expired(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert is_expired(future) is False

    def test_past_datetime_is_expired(self):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        assert is_expired(past) is True

    def test_treats_naive_as_utc(self):
        past = datetime(2020, 1, 1)
        assert is_expired(past) is True

    def test_future_naive_not_expired(self):
        future = datetime(2099, 1, 1)
        assert is_expired(future) is False

    def test_zero_datetime_is_expired(self):
        zero = datetime(2000, 1, 1, tzinfo=timezone.utc)
        assert is_expired(zero) is True


class TestComputeExpiry:
    def test_returns_future_datetime(self):
        expiry = compute_expiry(24)
        now = datetime.now(timezone.utc)
        assert expiry > now

    def test_returns_correct_hours(self):
        expiry = compute_expiry(1)
        now = datetime.now(timezone.utc)
        diff = (expiry - now).total_seconds()
        assert 3500 <= diff <= 3700  # ~1 hour with small tolerance

    def test_returns_timezone_aware(self):
        expiry = compute_expiry(12)
        assert expiry.tzinfo is not None
