"""Test suite for logging setup, including LoggerSetup and ColoredFormatter.

Tests include logging configuration in both debug and normal modes,
color formatting for log messages, and integration of log output.
"""

import io
import logging
import unittest
from unittest import mock

from typetrace.logging_setup import ColoredFormatter, LogColor, LoggerSetup


class TestLoggerSetup(unittest.TestCase):
    """Test suite for the LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""
        with self.assertRaises(TypeError):
            LoggerSetup()


class TestColoredFormatter(unittest.TestCase):
    """Test suite for the ColoredFormatter class."""

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        self.assertTrue(hasattr(formatter, "_ColoredFormatter__use_colors"))

    @mock.patch("platform.system")
    def test_should_use_colors_linux(self, mock_platform_system: mock.Mock) -> None:
        """Test color detection on Linux."""
        mock_platform_system.return_value = "Linux"
        formatter = ColoredFormatter()
        self.assertTrue(formatter._should_use_colors())

    @mock.patch("platform.system")
    def test_should_use_colors_darwin(self, mock_platform_system: mock.Mock) -> None:
        """Test color detection on macOS."""
        mock_platform_system.return_value = "Darwin"
        formatter = ColoredFormatter()
        self.assertTrue(formatter._should_use_colors())

    @mock.patch("platform.system")
    def test_should_use_colors_windows(self, mock_platform_system: mock.Mock) -> None:
        """Test color detection on Windows."""
        mock_platform_system.return_value = "Windows"
        formatter = ColoredFormatter()
        self.assertFalse(formatter._should_use_colors())

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=True)
    def test_format_with_colors(self, _mock_should_use_colors: mock.Mock) -> None:
        """Test formatting with colors enabled."""
        formatter = ColoredFormatter()

        record = logging.LogRecord("test", logging.WARNING, "", 0, "Test warning", (),
        None)
        formatted = formatter.format(record)
        self.assertIn(LogColor.YELLOW, formatted)
        self.assertIn(LogColor.RESET, formatted)

        record = logging.LogRecord("test", logging.ERROR, "", 0, "Test error", (), None)
        formatted = formatter.format(record)
        self.assertIn(LogColor.RED, formatted)
        self.assertIn(LogColor.RESET, formatted)

        record = logging.LogRecord("test", logging.INFO, "", 0, "Test info", (), None)
        formatted = formatter.format(record)
        self.assertNotIn(LogColor.YELLOW, formatted)
        self.assertNotIn(LogColor.RED, formatted)

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=False)
    def test_format_without_colors(self, _mock_should_use_colors: mock.Mock) -> None:
        """Test formatting with colors disabled."""
        formatter = ColoredFormatter()

        for level in [logging.INFO, logging.WARNING, logging.ERROR]:
            record = logging.LogRecord("test", level, "", 0, "Test message", (), None)
            formatted = formatter.format(record)
            self.assertNotIn(LogColor.YELLOW, formatted)
            self.assertNotIn(LogColor.RED, formatted)
            self.assertNotIn(LogColor.RESET, formatted)

    def test_format_with_non_string_msg(self) -> None:
        """Test formatting with a non-string message."""
        formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s")
        formatter._ColoredFormatter__use_colors = True

        record = logging.LogRecord(
            "test", logging.ERROR, "", 0, Exception("Test exception"), (), None,
        )
        formatted = formatter.format(record)
        self.assertIn(LogColor.RED + "ERROR" + LogColor.RESET, formatted)
        self.assertIn("Test exception", formatted)

    def test_log_output_integration(self) -> None:
        """Integration test for actual log output."""
        captured_output = io.StringIO()
        handler = logging.StreamHandler(captured_output)

        formatter = ColoredFormatter(fmt="%(levelname)s - %(message)s")
        formatter._ColoredFormatter__use_colors = True
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.propagate = False  # Avoid duplicate output

        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        captured_output.flush()
        output = captured_output.getvalue()
        lines = output.strip().split("\n")

        self.assertGreaterEqual(len(lines), 3)

        self.assertIn("INFO - Info message", lines[0])
        self.assertIn(f"{LogColor.YELLOW}WARNING{LogColor.RESET}", lines[1])
        self.assertIn(f"{LogColor.RED}ERROR{LogColor.RESET}", lines[2])


if __name__ == "__main__":
    unittest.main()
