"""Tests for the logging_setup module."""

import io
import logging
from unittest import mock

import pytest

from typetrace.backend.logging_setup import ColoredFormatter, LogColor, LoggerSetup


class TestLoggerSetup:
    """Test suite for the LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""
        with pytest.raises(TypeError):
            LoggerSetup()

    @mock.patch("typetrace.backend.logging_setup.Config")
    def test_setup_logging_debug_mode(self, mock_config: mock.MagicMock) -> None:
        """Test logging setup in debug mode.

        Args:
            mock_config: Mock for Config class.

        """
        mock_config.DEBUG = True

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)

        LoggerSetup.setup_logging()

        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, ColoredFormatter)

    @mock.patch("typetrace.config.Config")
    def test_setup_logging_normal_mode(self, mock_config: mock.MagicMock) -> None:
        """Test logging setup in normal (non-debug) mode.

        Args:
            mock_config: Mock for the Config class.

        """
        mock_config.DEBUG = False

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)

        LoggerSetup.setup_logging()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, ColoredFormatter)

    def test_setup_logging_multiple_calls(self) -> None:
        """Test that multiple calls to setup_logging don't add redundant handlers."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        LoggerSetup.setup_logging()
        LoggerSetup.setup_logging()
        LoggerSetup.setup_logging()

        # Only one handler should exist
        assert len(root_logger.handlers) == 1


class TestColoredFormatter:
    """Test suite for the ColoredFormatter class."""

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        assert hasattr(formatter, "_ColoredFormatter__use_colors")

    @mock.patch("platform.system")
    def test_should_use_colors_linux(
        self, mock_platform_system: mock.MagicMock
    ) -> None:
        """Test color detection on Linux.

        Args:
            mock_platform_system: Mock for platform.system.

        """
        mock_platform_system.return_value = "Linux"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors() is True

    @mock.patch("platform.system")
    def test_should_use_colors_darwin(
        self,
        mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on macOS.

        Args:
            mock_platform_system: Mock for platform.system.

        """
        mock_platform_system.return_value = "Darwin"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors() is True

    @mock.patch("platform.system")
    def test_should_use_colors_windows(
        self,
        mock_platform_system: mock.MagicMock,
    ) -> None:
        """Test color detection on Windows.

        Args:
            mock_platform_system: Mock for platform.system.

        """
        mock_platform_system.return_value = "Windows"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors() is False

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=True)
    def test_format_with_colors(self, mock_should_use_colors: mock.MagicMock) -> None:
        """Test formatting with colors enabled.

        Args:
            mock_should_use_colors: Mock for the _should_use_colors method.

        """
        formatter = ColoredFormatter()

        # Test warning level
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

        # Test error level
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

        # Test info level (no colors)
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

    @mock.patch.object(ColoredFormatter, "_should_use_colors", return_value=False)
    def test_format_without_colors(
        self,
        mock_should_use_colors: mock.MagicMock,
    ) -> None:
        """Test formatting with colors disabled.

        Args:
            mock_should_use_colors: Mock for the _should_use_colors method.

        """
        formatter = ColoredFormatter()

        # Test with different log levels
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
        """Test formatting with a non-string message.

        The message type should be colored whereas the exception message itself
        should not be colored.
        """
        formatter = ColoredFormatter(fmt="%(levelname)s: %(message)s")
        formatter._ColoredFormatter__use_colors = True

        # Test with a non-string message (like an exception or integer)
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=Exception("Test exception"),
            args=(),
            exc_info=None,
        )

        # This should not raise an exception
        formatted = formatter.format(record)

        assert f"{LogColor.RED}ERROR{LogColor.RESET}" in formatted

        # The exception message itself should not be colored
        exception_text = str(Exception("Test exception"))
        assert exception_text in formatted

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

        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        output = captured_output.getvalue()

        lines = output.strip().split("\n")
        assert "INFO - Info message" in lines[0]
        assert f"{LogColor.YELLOW}WARNING{LogColor.RESET}" in lines[1]
        assert f"{LogColor.RED}ERROR{LogColor.RESET}" in lines[2]
