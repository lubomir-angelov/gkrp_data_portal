"""Tests for gkrp_data_portal.core.email."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from gkrp_data_portal.core.email import maybe_send_invite_email


class TestMaybeSendInviteEmail:
    def test_skips_when_smtp_not_configured(self):
        with patch("gkrp_data_portal.core.email.get_smtp_settings", return_value=None):
            result = maybe_send_invite_email(
                to_email="test@example.com",
                subject="Test",
                body="Body",
            )
            assert result is False

    def test_sends_with_tls(self):
        smtp = MagicMock()
        smtp.host = "smtp.example.com"
        smtp.port = 587
        smtp.username = "user"
        smtp.password = "pass"
        smtp.sender = "from@example.com"
        smtp.use_tls = True

        mock_smtp_instance = MagicMock()

        def make_smtp(*args, **kwargs):
            mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
            mock_smtp_instance.__exit__ = MagicMock(return_value=False)
            return mock_smtp_instance

        with patch("gkrp_data_portal.core.email.get_smtp_settings", return_value=smtp):
            with patch(
                "gkrp_data_portal.core.email.smtplib.SMTP", side_effect=make_smtp
            ):
                result = maybe_send_invite_email(
                    to_email="test@example.com",
                    subject="Test Subject",
                    body="Test Body",
                )
                assert result is True
                mock_smtp_instance.ehlo.assert_called()
                mock_smtp_instance.starttls.assert_called_once()

    def test_sends_without_tls(self):
        smtp = MagicMock()
        smtp.host = "smtp.example.com"
        smtp.port = 25
        smtp.username = "user"
        smtp.password = "pass"
        smtp.sender = "from@example.com"
        smtp.use_tls = False

        mock_smtp_instance = MagicMock()

        def make_smtp(*args, **kwargs):
            mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
            mock_smtp_instance.__exit__ = MagicMock(return_value=False)
            return mock_smtp_instance

        with patch("gkrp_data_portal.core.email.get_smtp_settings", return_value=smtp):
            with patch(
                "gkrp_data_portal.core.email.smtplib.SMTP", side_effect=make_smtp
            ):
                result = maybe_send_invite_email(
                    to_email="test@example.com",
                    subject="Test",
                    body="Body",
                )
                assert result is True
                mock_smtp_instance.ehlo.assert_called()
                mock_smtp_instance.starttls.assert_not_called()

    def test_returns_false_on_exception(self):
        smtp = MagicMock()
        smtp.host = "smtp.example.com"
        smtp.port = 587
        smtp.username = "user"
        smtp.password = "pass"
        smtp.sender = "from@example.com"
        smtp.use_tls = True

        with patch("gkrp_data_portal.core.email.get_smtp_settings", return_value=smtp):
            with patch(
                "gkrp_data_portal.core.email.smtplib.SMTP",
                side_effect=Exception("connection failed"),
            ):
                result = maybe_send_invite_email(
                    to_email="test@example.com",
                    subject="Test",
                    body="Body",
                )
                assert result is False
