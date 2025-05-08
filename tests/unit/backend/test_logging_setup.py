"""Test suite for logging setup, including LoggerSetup and ColoredFormatter.

Tests include logging configuration in both debug and normal modes,
color formatting for log messages, and integration of log output.
"""

import logging
from unittest import TestCase, mock

import pytest

from typetrace.logging_setup import ColoredFormatter, LogColor


class TestLoggerSetup(TestCase):
    """Test suite for the LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""

    """Test suite for the ColoredFormatter class."""

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        assert hasattr(formatter, "_ColoredFormatter__use_colors")

    @mock.patch("platform.system")
    def test_should_use_colors_linux(
        self,
        mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on Linux."""
        mock_platform_system.return_value = "Linux"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors()

    @mock.patch("platform.system")
    def test_should_use_colors_darwin(
        self,
        mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on macOS."""
        mock_platform_system.return_value = "Darwin"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors()

    @mock.patch("platform.system")
    def test_should_use_colors_windows(
        self,
        mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on Windows."""
        mock_platform_system.return_value = "Windows"
        formatter = ColoredFormatter()
        assert not formatter._should_use_colors()

    @pytest.mark.usefixtures("_mock_should_use_colors")
    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=True)
    def test_format_with_colors(
        self,
    ) -> None:
        """Test formatting with colors enabled."""
        formatter = ColoredFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Test warning",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert LogColor.YELLOW in formatted
        assert LogColor.RESET in formatted

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert LogColor.RED in formatted
        assert LogColor.RESET in formatted

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test info",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert LogColor.YELLOW not in formatted
        assert LogColor.RED not in formatted

    @pytest.mark.usefixtures("_mock_should_use_colors")
    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=False)
    def test_format_without_colors(
        self,
    ) -> None:
        """Test formatting with colors disabled."""
        formatter = ColoredFormatter()

        for level in [logging.INFO, logging.WARNING, logging.ERROR]:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            formatted = formatter.format(record)
            assert LogColor.YELLOW not in formatted
            assert LogColor.RED not in formatted
            assert LogColor.RESET not in formatted

    def test_format_with_non_string_msg(self) -> None:
        """Test formatting with a non-string message."""
        formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s")
        formatter._ColoredFormatter__use_colors = True

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=Exception("Test exception"),
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        assert LogColor.RED + "ERROR" + LogColor.RESET in formatted
        exception_text = str(Exception("Test exception"))
        assert exception_text in formatted
