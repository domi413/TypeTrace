"""Test suite for logging setup, including LoggerSetup and ColoredFormatter.

Tests include logging configuration in both debug and normal modes,
color formatting for log messages, and integration of log output.
"""

import io
import logging
from unittest import TestCase, mock

from typetrace.logging_setup import ColoredFormatter, LogColor, LoggerSetup


class TestLoggerSetup(TestCase):
    """Test suite for the LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""
        with self.assertRaises(TypeError):  # noqa: PT027
            LoggerSetup()


class TestColoredFormatter(TestCase):
    """Test suite for the ColoredFormatter class."""

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        self.assertTrue(hasattr(formatter, "_ColoredFormatter__use_colors"))

    @mock.patch("platform.system")
    def test_should_use_colors_linux(
        self, mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on Linux."""
        mock_platform_system.return_value = "Linux"
        formatter = ColoredFormatter()
        self.assertTrue(formatter._should_use_colors())

    @mock.patch("platform.system")
    def test_should_use_colors_darwin(
        self, mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on macOS."""
        mock_platform_system.return_value = "Darwin"
        formatter = ColoredFormatter()
        self.assertTrue(formatter._should_use_colors())

    @mock.patch("platform.system")
    def test_should_use_colors_windows(
        self, mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on Windows."""
        mock_platform_system.return_value = "Windows"
        formatter = ColoredFormatter()
        self.assertFalse(formatter._should_use_colors())

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=True)
    def test_format_with_colors(
        self, _mock_should_use_colors: mock.MagicMock,  # noqa: PT019
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
        self.assertIn(LogColor.YELLOW, formatted)
        self.assertIn(LogColor.RESET, formatted)

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
        self.assertIn(LogColor.RED, formatted)
        self.assertIn(LogColor.RESET, formatted)

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
        self.assertNotIn(LogColor.YELLOW, formatted)
        self.assertNotIn(LogColor.RED, formatted)

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=False)
    def test_format_without_colors(
        self, _mock_should_use_colors: mock.MagicMock,  # noqa: PT019
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
            self.assertNotIn(LogColor.YELLOW, formatted)
            self.assertNotIn(LogColor.RED, formatted)
            self.assertNotIn(LogColor.RESET, formatted)

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

        self.assertIn(LogColor.RED + "ERROR" + LogColor.RESET, formatted)
        exception_text = str(Exception("Test exception"))
        self.assertIn(exception_text, formatted)

    