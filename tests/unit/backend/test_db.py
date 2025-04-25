"""Test suite for logging setup, including LoggerSetup and ColoredFormatter."""

import logging
from unittest import TestCase, mock

from typetrace.backend.logging_setup import ColoredFormatter, LogColor, LoggerSetup


class TestLoggerSetup(TestCase):
    """Test suite for the LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""
        with self.assertRaises(TypeError):  # noqa: PT027
            LoggerSetup()

    @mock.patch("typetrace.backend.logging_setup.Config")
    def test_setup_logging_debug_mode(self, mock_config: mock.MagicMock) -> None:
        """Test logging setup in debug mode."""
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
        assert handler.formatter._fmt == "%(asctime)s - %(levelname)s - %(message)s"
        assert handler.formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    @mock.patch("typetrace.backend.logging_setup.Config")
    def test_setup_logging_normal_mode(self, mock_config: mock.MagicMock) -> None:
        """Test logging setup in normal (non-debug) mode."""
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
        assert handler.formatter._fmt == "%(asctime)s - %(levelname)s - %(message)s"
        assert handler.formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    @mock.patch("typetrace.backend.logging_setup.Config")
    def test_setup_logging_multiple_calls(self, mock_config: mock.MagicMock) -> None:
        """Test that multiple calls to setup_logging don't add redundant handlers."""
        mock_config.DEBUG = False

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.NOTSET)

        LoggerSetup.setup_logging()
        LoggerSetup.setup_logging()
        LoggerSetup.setup_logging()

        assert len(root_logger.handlers) == 1
        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert isinstance(handler.formatter, ColoredFormatter)
        assert handler.formatter._fmt == "%(asctime)s - %(levelname)s - %(message)s"
        assert handler.formatter.datefmt == "%Y-%m-%d %H:%M:%S"
        assert root_logger.level == logging.INFO


class TestColoredFormatter(TestCase):
    """Test suite for the ColoredFormatter class."""

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        assert hasattr(formatter, "_ColoredFormatter__use_colors")

    @mock.patch("platform.system")
    def test_should_use_colors_linux(
        self, mock_platform_system: mock.MagicMock
    ) -> None:
        """Test color detection on Linux."""
        mock_platform_system.return_value = "Linux"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors()

    @mock.patch("platform.system")
    def test_should_use_colors_darwin(
        self, mock_platform_system: mock.MagicMock
    ) -> None:
        """Test color detection on macOS."""
        mock_platform_system.return_value = "Darwin"
        formatter = ColoredFormatter()
        assert formatter._should_use_colors()

    @mock.patch("platform.system")
    def test_should_use_colors_windows(
        self, mock_platform_system: mock.MagicMock
    ) -> None:
        """Test color detection on Windows."""
        mock_platform_system.return_value = "Windows"
        formatter = ColoredFormatter()
        assert not formatter._should_use_colors()

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
