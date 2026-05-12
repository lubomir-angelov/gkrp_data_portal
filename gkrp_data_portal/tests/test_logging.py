"""Tests for gkrp_data_portal.core.logging."""

from __future__ import annotations

import logging
from unittest.mock import patch

from gkrp_data_portal.core.logging import configure_logging


class TestConfigureLogging:
    def test_defaults_to_info(self):
        with patch("logging.basicConfig") as mock_basic_config:
            configure_logging()
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == logging.INFO

    def test_respects_log_level_env(self):
        with patch("logging.basicConfig") as mock_basic_config:
            with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
                configure_logging()
                call_kwargs = mock_basic_config.call_args[1]
                assert call_kwargs["level"] == logging.DEBUG

    def test_respects_uppercase_log_level(self):
        with patch("logging.basicConfig") as mock_basic_config:
            with patch.dict("os.environ", {"LOG_LEVEL": "warning"}):
                configure_logging()
                call_kwargs = mock_basic_config.call_args[1]
                assert call_kwargs["level"] == logging.WARNING

    def test_uses_default_for_invalid_level(self):
        with patch("logging.basicConfig") as mock_basic_config:
            with patch.dict("os.environ", {"LOG_LEVEL": "INVALID_LEVEL_XYZ"}):
                configure_logging()
                call_kwargs = mock_basic_config.call_args[1]
                assert call_kwargs["level"] == logging.INFO

    def test_sets_format(self):
        with patch("logging.basicConfig") as mock_basic_config:
            configure_logging()
            call_kwargs = mock_basic_config.call_args[1]
            assert (
                call_kwargs["format"]
                == "%(asctime)s %(levelname)s %(name)s - %(message)s"
            )
