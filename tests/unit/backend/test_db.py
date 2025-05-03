"""Tests for the backend database module."""

import logging
import sqlite3
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from typetrace.backend.db import DatabaseManager
from typetrace.backend.logging_setup import ColoredFormatter, LoggerSetup
from typetrace.config import Config
from typetrace.sql import SQLQueries


class TestDatabaseManager(unittest.TestCase):
    """Test suite for the DatabaseManager class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.db_manager = DatabaseManager()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_db_path = Path(self.temp_dir.name) / Config.DB_NAME

    def tearDown(self) -> None:
        """Clean up after each test method."""
        self.temp_dir.cleanup()

    def test_initialize_database(self) -> None:
        """Test database initialization."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            self.db_manager.initialize_database(self.mock_db_path)

            mock_connect.assert_called_once_with(self.mock_db_path)
            mock_cursor.execute.assert_called_once_with(SQLQueries.CREATE_KEYSTROKES_TABLE)
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_initialize_database_sqlite_error(self) -> None:
        """Test database initialization with SQLite error."""
        with patch("sqlite3.connect") as mock_connect, \
             patch("typetrace.backend.db.logger") as mock_logger:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

            with self.assertRaises(sqlite3.Error) as cm:  # noqa: PT027
                self.db_manager.initialize_database(self.mock_db_path)
            self.assertEqual(str(cm.exception), "Mock SQLite error")

            mock_conn.close.assert_called_once()
            mock_logger.exception.assert_called_once_with("Database error")

    def test_initialize_database_operational_error(self) -> None:
        """Test database initialization with SQLite operational error."""
        with patch("sqlite3.connect") as mock_connect, \
             patch("typetrace.backend.db.logger") as mock_logger:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.OperationalError(
                "Mock operational error",
            )

            with self.assertRaises(sqlite3.OperationalError) as cm:  # noqa: PT027
                self.db_manager.initialize_database(self.mock_db_path)
            self.assertEqual(str(cm.exception), "Mock operational error")

            mock_conn.close.assert_called_once()
            mock_logger.exception.assert_called_once_with("SQLite operational error")

    def test_write_to_database_empty_events(self) -> None:
        """Test write_to_database with empty events list."""
        with patch("sqlite3.connect") as mock_connect:
            self.db_manager.write_to_database(self.mock_db_path, [])
            mock_connect.assert_not_called()

    def test_write_to_database_with_events(self) -> None:
        """Test write_to_database with events list."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            input_events = [
                {"scan_code": 30, "name": "KEY_A", "date": "2025-04-22"},
                {"scan_code": 42, "name": "KEY_LEFTSHIFT", "date": "2025-04-22"},
            ]

            expected_processed_events = [
                {"scan_code": 30, "key_name": "KEY_A", "date": "2025-04-22"},
                {"scan_code": 42, "key_name": "KEY_LEFTSHIFT", "date": "2025-04-22"},
            ]

            self.db_manager.write_to_database(self.mock_db_path, input_events)
            mock_connect.assert_called_once_with(self.mock_db_path)

            mock_cursor.executemany.assert_called_once_with(
                SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
                expected_processed_events,
            )

            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_write_to_database_sqlite_error(self) -> None:
        """Test write_to_database with SQLite error."""
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.executemany.side_effect = sqlite3.Error("Mock SQLite error")

            input_events = [{"scan_code": 30, "name": "KEY_A", "date": "2025-04-22"}]

            stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                with self.assertRaises(sqlite3.Error) as cm:  # noqa: PT027
                    self.db_manager.write_to_database(self.mock_db_path, input_events)
                self.assertEqual(str(cm.exception), "Mock SQLite error")
            finally:
                sys.stderr = stderr

            mock_conn.close.assert_called_once()

    def test_write_to_database_with_invalid_characters(self) -> None:
        """Test write_to_database with events containing invalid characters.

        This is a test-case that should not happen in a real-world scenario,
        since the following are not valid keyboard inputs.
        """
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            input_events = [
                {
                    "scan_code": 30,
                    "name": "KEY_A;DROP TABLE keystrokes;",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 42,
                    "name": "KEY_'\"\\",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 44,
                    "name": "KEY_\u2022\u00a9\u00ae",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 45,
                    "name": ("MULTI", "KEY", "COMBO"),
                    "date": "2025-04-22",
                },
            ]

            expected_processed_events = [
                {
                    "scan_code": 30,
                    "key_name": "KEY_A;DROP TABLE keystrokes;",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 42,
                    "key_name": "KEY_'\"\\",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 44,
                    "key_name": "KEY_\u2022\u00a9\u00ae",
                    "date": "2025-04-22",
                },
                {
                    "scan_code": 45,
                    "key_name": "MULTI, KEY, COMBO",
                    "date": "2025-04-22",
                },
            ]

            self.db_manager.write_to_database(self.mock_db_path, input_events)
            mock_connect.assert_called_once_with(self.mock_db_path)

            mock_cursor.executemany.assert_called_once_with(
                SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
                expected_processed_events,
            )

            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()


class TestColoredFormatter(unittest.TestCase):
    """Test suite for ColoredFormatter class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.formatter = ColoredFormatter()

    def test_formatter_initialization(self) -> None:
        """Test ColoredFormatter initialization."""
        formatter = ColoredFormatter()
        self.assertIsInstance(formatter, logging.Formatter)

    def test_format_without_colors(self) -> None:
        """Test formatting with colors disabled."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        self.assertNotIn("\033[32m", formatted)

    def test_format_with_non_string_msg(self) -> None:
        """Test formatting with a non-string message."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=123,
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        self.assertIn("123", formatted)


class TestLoggerSetup(unittest.TestCase):
    """Test suite for LoggerSetup class."""

    def test_logger_setup_instantiation_fails(self) -> None:
        """Test that LoggerSetup cannot be instantiated."""
        with self.assertRaises(TypeError):  # noqa: PT027
            LoggerSetup()


if __name__ == "__main__":
    unittest.main()
