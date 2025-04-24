"""Tests for the backend database module."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

from typetrace.backend.db import DatabaseManager
from typetrace.backend.sql import SQLQueries

if TYPE_CHECKING:
    from typetrace.config import Event


class TestDatabaseManager(unittest.TestCase):
    """Test suite for the DatabaseManager class."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.db_manager = DatabaseManager()
        # Create a temporary directory for the mock database path
        self.temp_dir = tempfile.mkdtemp()
        from typetrace.config import Config

        self.mock_db_path = Path(self.temp_dir) / Config.DB_NAME

    def tearDown(self):
        """Clean up the test environment after each test."""
        import shutil

        shutil.rmtree(self.temp_dir)

    # ==========================================================
    # ========== Tests for initialize_database method ==========
    # ==========================================================
    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_initialize_database(
        self, mock_connect: mock.MagicMock, mock_logger: mock.MagicMock,
    ) -> None:
        """Test database initialization."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        self.db_manager.initialize_database(self.mock_db_path)

        mock_connect.assert_called_once_with(self.mock_db_path)
        mock_cursor.execute.assert_called_once_with(SQLQueries.CREATE_KEYSTROKES_TABLE)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        mock_logger.debug.assert_called_once_with(
            "Database initialized at %s", self.mock_db_path,
        )

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_initialize_database_sqlite_error(
        self, mock_connect: mock.MagicMock, mock_logger: mock.MagicMock,
    ) -> None:
        """Test database initialization with SQLite error."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

        with self.pytest.raises(sqlite3.Error, "Mock SQLite error"):
            self.db_manager.initialize_database(self.mock_db_path)

        mock_conn.close.assert_called_once()
        mock_logger.exception.assert_called_once_with("Database error")

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_initialize_database_operational_error(
        self, mock_connect: mock.MagicMock, mock_logger: mock.MagicMock,
    ) -> None:
        """Test database initialization with SQLite operational error."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.OperationalError(
            "Mock operational error",
        )

        with self.assertRaisesRegex(sqlite3.OperationalError, "Mock operational error"):
            self.db_manager.initialize_database(self.mock_db_path)

        mock_conn.close.assert_called_once()
        mock_logger.exception.assert_called_once_with("SQLite operational error")

    # ========================================================
    # ========== Tests for write_to_database method ==========
    # ========================================================
    @mock.patch("sqlite3.connect")
    def test_write_to_database_empty_events(self, mock_connect: mock.MagicMock) -> None:
        """Test write_to_database with empty events list."""
        self.db_manager.write_to_database(self.mock_db_path, [])

        mock_connect.assert_not_called()

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_write_to_database_with_events(
        self, mock_connect: mock.MagicMock, mock_logger: mock.MagicMock,
    ) -> None:
        """Test write_to_database with events list."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        input_events: list[Event] = [
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
        mock_logger.debug.assert_called_once_with(
            "Updated database with %d keystroke events", len(input_events),
        )

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_write_to_database_sqlite_error(
        self, mock_connect: mock.MagicMock, mock_logger: mock.MagicMock,
    ) -> None:
        """Test write_to_database with SQLite error."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.executemany.side_effect = sqlite3.Error("Mock SQLite error")

        input_events: list[Event] = [
            {"scan_code": 30, "name": "KEY_A", "date": "2025-04-22"},
        ]

        with self.assertRaisesRegex(sqlite3.Error, "Mock SQLite error"):
            self.db_manager.write_to_database(self.mock_db_path, input_events)

        mock_conn.close.assert_called_once()
        mock_logger.exception.assert_called_once_with("Database error")

    @mock.patch("sqlite3.connect")
    def test_write_to_database_with_invalid_characters(
        self, mock_connect: mock.MagicMock,
    ) -> None:
        """Test write_to_database with events containing invalid characters."""
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        input_events: list[Event] = [
            {
                "scan_code": 30,
                "name": "KEY_A;DROP TABLE keystrokes;",
                "date": "2025-04-22",
            },  # SQL injection attempt
            {
                "scan_code": 42,
                "name": "KEY_'\"\\",
                "date": "2025-04-22",
            },  # Quote characters
            {
                "scan_code": 44,
                "name": "KEY_\u2022\u00a9\u00ae",
                "date": "2025-04-22",
            },  # Unicode characters
            {
                "scan_code": 45,
                "name": ("MULTI", "KEY", "COMBO"),
                "date": "2025-04-22",
            },  # Tuple of names
        ]

        expected_processed_events = [
            {
                "scan_code": 30,
                "key_name": "KEY_A;DROP TABLE keystrokes;",
                "date": "2025-04-22",
            },
            {"scan_code": 42, "key_name": "KEY_'\"\\", "date": "2025-04-22"},
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


if __name__ == "__main__":
    unittest.main()
