"""Tests for the backend database module."""

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from typetrace.backend.db import DatabaseManager
from typetrace.backend.sql import SQLQueries

if TYPE_CHECKING:
    from typetrace.config import Event


class TestDatabaseManager:
    """Test suite for the DatabaseManager class."""

    @pytest.fixture
    def db_manager(self) -> DatabaseManager:
        """Provide a DatabaseManager instance for testing.

        Returns:
            A fresh DatabaseManager instance.

        """
        return DatabaseManager()

    @pytest.fixture
    def mock_db_path(self, tmp_path: Path) -> Path:
        """Provide a mock database path.

        Args:
            tmp_path: Pytest's temporary directory fixture.

        Returns:
            A Path object for a mock database.

        """
        from typetrace.config import Config

        return tmp_path / Config.DB_NAME

    # ==========================================================
    # ========== Tests for initialize_database method ==========
    # ==========================================================
    @mock.patch("sqlite3.connect")
    def test_initialize_database(
        self,
        mock_connect: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test database initialization.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        db_manager.initialize_database(mock_db_path)

        mock_connect.assert_called_once_with(mock_db_path)
        mock_cursor.execute.assert_called_once_with(SQLQueries.CREATE_KEYSTROKES_TABLE)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_initialize_database_sqlite_error(
        self,
        mock_connect: mock.MagicMock,
        mock_logger: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test database initialization with SQLite error.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            mock_logger: Mock for database logger
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

        with pytest.raises(sqlite3.Error, match="Mock SQLite error"):
            db_manager.initialize_database(mock_db_path)

        mock_conn.close.assert_called_once()
        mock_logger.exception.assert_called_once_with("Database error")

    @mock.patch("typetrace.backend.db.logger")
    @mock.patch("sqlite3.connect")
    def test_initialize_database_operational_error(
        self,
        mock_connect: mock.MagicMock,
        mock_logger: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test database initialization with SQLite error.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            mock_logger: Mock for database logger
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.OperationalError(
            "Mock operational error",
        )

        with pytest.raises(sqlite3.OperationalError, match="Mock operational error"):
            db_manager.initialize_database(mock_db_path)

        mock_conn.close.assert_called_once()
        mock_logger.exception.assert_called_once_with("SQLite operational error")

    # ========================================================
    # ========== Tests for write_to_database method ==========
    # ========================================================
    @mock.patch("sqlite3.connect")
    def test_write_to_database_empty_events(
        self,
        mock_connect: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test write_to_database with empty events list.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        db_manager.write_to_database(mock_db_path, [])

        mock_connect.assert_not_called()

    @mock.patch("sqlite3.connect")
    def test_write_to_database_with_events(
        self,
        mock_connect: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test write_to_database with events list.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        input_events: list[Event] = [
            {"scan_code": 30, "name": "KEY_A"},
            {"scan_code": 42, "name": "KEY_LEFTSHIFT"},
        ]

        expected_processed_events = [
            {"scan_code": 30, "key_name": "KEY_A"},
            {"scan_code": 42, "key_name": "KEY_LEFTSHIFT"},
        ]

        db_manager.write_to_database(mock_db_path, input_events)
        mock_connect.assert_called_once_with(mock_db_path)

        mock_cursor.executemany.assert_called_once_with(
            SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
            expected_processed_events,
        )

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @mock.patch("sqlite3.connect")
    def test_write_to_database_sqlite_error(
        self,
        mock_connect: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test write_to_database with SQLite error.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.executemany.side_effect = sqlite3.Error("Mock SQLite error")

        input_events: list[Event] = [{"scan_code": 30, "name": "KEY_A"}]

        with pytest.raises(sqlite3.Error, match="Mock SQLite error"):
            db_manager.write_to_database(mock_db_path, input_events)

        mock_conn.close.assert_called_once()

    @mock.patch("sqlite3.connect")
    def test_write_to_database_with_invalid_characters(
        self,
        mock_connect: mock.MagicMock,
        db_manager: DatabaseManager,
        mock_db_path: Path,
    ) -> None:
        """Test write_to_database with events containing invalid characters.

            This is a test-case that should not happen in a real-world scenario,
            since the following are not valid keyboard inputs.

        Args:
            mock_connect: Mock for sqlite3.connect function.
            db_manager: DatabaseManager instance fixture.
            mock_db_path: Mock database path fixture.

        """
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        input_events: list[Event] = [
            {
                "scan_code": 30,
                "name": "KEY_A;DROP TABLE keystrokes;",
            },  # SQL injection attempt
            {"scan_code": 42, "name": "KEY_'\"\\"},  # Quote characters
            {"scan_code": 44, "name": "KEY_\u2022\u00a9\u00ae"},  # Unicode characters
            {"scan_code": 45, "name": ("MULTI", "KEY", "COMBO")},  # Tuple of names
        ]

        expected_processed_events = [
            {"scan_code": 30, "key_name": "KEY_A;DROP TABLE keystrokes;"},
            {"scan_code": 42, "key_name": "KEY_'\"\\"},
            {"scan_code": 44, "key_name": "KEY_\u2022\u00a9\u00ae"},
            {
                "scan_code": 45,
                "key_name": "MULTI, KEY, COMBO",
            },
        ]

        db_manager.write_to_database(mock_db_path, input_events)
        mock_connect.assert_called_once_with(mock_db_path)

        mock_cursor.executemany.assert_called_once_with(
            SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
            expected_processed_events,
        )

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
