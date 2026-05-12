"""Tests for gkrp_data_portal.core.settings."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from gkrp_data_portal.core.settings import (
    SmtpSettings,
    get_app_base_url,
    get_database_url,
    get_invite_ttl_hours,
    get_secret_key,
    get_smtp_settings,
    get_storage_secret,
)


class TestGetDatabaseUrl:
    def test_returns_url_when_set(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/db"}):
            assert get_database_url() == "postgresql://localhost/db"

    def test_raises_when_missing(self):
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
                get_database_url()


class TestGetSecretKey:
    def test_returns_key_when_set(self):
        with patch.dict(os.environ, {"SECRET_KEY": "my-secret"}):
            assert get_secret_key() == "my-secret"

    def test_raises_when_missing(self):
        env = os.environ.copy()
        env.pop("SECRET_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="SECRET_KEY is not set"):
                get_secret_key()


class TestGetAppBaseUrl:
    def test_returns_base_without_trailing_slash(self):
        with patch.dict(os.environ, {"APP_BASE_URL": "http://localhost:8080/"}):
            assert get_app_base_url() == "http://localhost:8080"

    def test_returns_default_when_missing(self):
        env = os.environ.copy()
        env.pop("APP_BASE_URL", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_app_base_url() == "http://localhost:8080"

    def test_strips_multiple_trailing_slashes(self):
        with patch.dict(os.environ, {"APP_BASE_URL": "http://example.com///"}):
            assert get_app_base_url() == "http://example.com"


class TestGetInviteTtlHours:
    def test_returns_valid_int(self):
        with patch.dict(os.environ, {"INVITE_TTL_HOURS": "48"}):
            assert get_invite_ttl_hours() == 48

    def test_clamps_to_minimum_1(self):
        with patch.dict(os.environ, {"INVITE_TTL_HOURS": "0"}):
            assert get_invite_ttl_hours() == 1

    def test_returns_default_72_when_missing(self):
        env = os.environ.copy()
        env.pop("INVITE_TTL_HOURS", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_invite_ttl_hours() == 72

    def test_returns_default_on_invalid_value(self):
        with patch.dict(os.environ, {"INVITE_TTL_HOURS": "abc"}):
            assert get_invite_ttl_hours() == 72

    def test_handles_negative(self):
        with patch.dict(os.environ, {"INVITE_TTL_HOURS": "-5"}):
            assert get_invite_ttl_hours() == 1


class TestGetStorageSecret:
    def test_returns_env_value(self):
        with patch.dict(os.environ, {"STORAGE_SECRET": "custom-secret"}):
            assert get_storage_secret() == "custom-secret"

    def test_returns_default_when_missing(self):
        env = os.environ.copy()
        env.pop("STORAGE_SECRET", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_storage_secret() == "dev-insecure-secret-change-me"


class TestGetSmtpSettings:
    def test_returns_none_when_missing_fields(self):
        env = os.environ.copy()
        env.pop("SMTP_HOST", None)
        env.pop("SMTP_PORT", None)
        env.pop("SMTP_USERNAME", None)
        env.pop("SMTP_PASSWORD", None)
        env.pop("SMTP_FROM", None)
        with patch.dict(os.environ, env, clear=True):
            assert get_smtp_settings() is None

    def test_returns_smtp_settings_when_all_set(self):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USERNAME": "user",
                "SMTP_PASSWORD": "pass",
                "SMTP_FROM": "sender@example.com",
            },
        ):
            result = get_smtp_settings()
            assert isinstance(result, SmtpSettings)
            assert result.host == "smtp.example.com"
            assert result.port == 587
            assert result.username == "user"
            assert result.password == "pass"
            assert result.sender == "sender@example.com"
            assert result.use_tls is True

    def test_returns_smtp_settings_with_tls_disabled(self):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "25",
                "SMTP_USERNAME": "user",
                "SMTP_PASSWORD": "pass",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "false",
            },
        ):
            result = get_smtp_settings()
            assert result is not None
            assert result.use_tls is False

    def test_returns_none_on_invalid_port(self):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "not-a-port",
                "SMTP_USERNAME": "user",
                "SMTP_PASSWORD": "pass",
                "SMTP_FROM": "sender@example.com",
            },
        ):
            assert get_smtp_settings() is None

    @pytest.mark.parametrize("tls_val", ["1", "true", "yes", "y"])
    def test_tls_enabled_variants(self, tls_val):
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.example.com",
                "SMTP_PORT": "587",
                "SMTP_USERNAME": "user",
                "SMTP_PASSWORD": "pass",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": tls_val,
            },
        ):
            result = get_smtp_settings()
            assert result is not None
            assert result.use_tls is True
