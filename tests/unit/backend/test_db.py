"""Tests for the DatabaseManager class."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from typetrace.backend.db import DatabaseManager
from typetrace.sql import SQLQueries

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import Mock

    from pytest_mock import MockerFixture

    from typetrace.config import Event


@pytest.fixture()
def db_manager() -> DatabaseManager:
    """Provide a DatabaseManager instance for testing."""
    return DatabaseManager()


@pytest.fixture()
def mock_db_path(tmp_path: Path) -> Path:
    """Provide a mock database path."""
    return tmp_path / "test.db"


@pytest.fixture()
def mock_sqlite(mocker: MockerFixture) -> tuple[Mock, Mock]:
    """Mock SQLite connection and cursor."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch("sqlite3.connect", return_value=mock_conn)
    return mock_conn, mock_cursor


# =============================================================================
# =================== Tests for initialize_database method ====================
# =============================================================================
def test_initialize_database(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mock_sqlite: tuple[Mock, Mock],
) -> None:
    """Test database initialization creates the keystrokes table."""
    mock_conn, mock_cursor = mock_sqlite
    mock_conn, mock_cursor = mock_sqlite
    db_manager.initialize_database(mock_db_path)

    mock_cursor.execute.assert_called_once_with(SQLQueries.CREATE_KEYSTROKES_TABLE)
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@pytest.mark.parametrize(
    ("error_type", "error_msg"),
    [
        (sqlite3.Error, "Mock SQLite error"),
        (sqlite3.OperationalError, "Mock operational error"),
    ],
)
def test_init_fails_on_error(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mock_sqlite: tuple[Mock, Mock],
    error_type: type[Exception],
    error_msg: str,
) -> None:
    """Test database initialization handles SQLite errors."""
    mock_conn, mock_cursor = mock_sqlite
    mock_cursor.execute.side_effect = error_type(error_msg)

    with pytest.raises(error_type, match=error_msg):
        db_manager.initialize_database(mock_db_path)

    mock_conn.close.assert_called_once()


# =============================================================================
# ========================= Tests for write method ============================
# =============================================================================
def test_write_events(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mock_sqlite: tuple[Mock, Mock],
) -> None:
    """Test writing events to the database."""
    mock_conn, mock_cursor = mock_sqlite
    input_events: list[Event] = [
        {"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"},
        {"scan_code": 42, "name": "KEY_LEFTSHIFT", "date": "2022-01-01"},
    ]
    expected = [
        {"scan_code": 30, "key_name": "KEY_A", "date": "2022-01-01"},
        {"scan_code": 42, "key_name": "KEY_LEFTSHIFT", "date": "2022-01-01"},
    ]

    db_manager.write_to_database(mock_db_path, input_events)

    mock_cursor.executemany.assert_called_once_with(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        expected,
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def test_write_no_events(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test writing an empty events list does nothing."""
    mock_connect = mocker.patch("sqlite3.connect")
    db_manager.write_to_database(mock_db_path, [])
    mock_connect.assert_not_called()


def test_write_fails_on_sqlite_error(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mock_sqlite: tuple[Mock, Mock],
) -> None:
    """Test writing events handles SQLite errors."""
    mock_conn, mock_cursor = mock_sqlite
    mock_cursor.executemany.side_effect = sqlite3.Error("Mock SQLite error")
    input_events: list[Event] = [
        {"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"},
    ]

    with pytest.raises(sqlite3.Error, match="Mock SQLite error"):
        db_manager.write_to_database(mock_db_path, input_events)

    mock_conn.close.assert_called_once()


def test_write_special_characters(
    db_manager: DatabaseManager,
    mock_db_path: Path,
    mock_sqlite: tuple[Mock, Mock],
) -> None:
    """Test writing events with special characters."""
    mock_conn, mock_cursor = mock_sqlite
    input_events: list[Event] = [
        {"scan_code": 30, "name": "KEY_A;DROP TABLE keystrokes;", "date": "2022-01-01"},
        {"scan_code": 42, "name": "KEY_'\"\\", "date": "2022-01-01"},
        {"scan_code": 44, "name": "KEY_\u2022\u00a9\u00ae", "date": "2022-01-01"},
        {"scan_code": 45, "name": ("MULTI", "KEY", "COMBO"), "date": "2022-01-01"},
    ]
    expected = [
        {
            "scan_code": 30,
            "key_name": "KEY_A;DROP TABLE keystrokes;",
            "date": "2022-01-01",
        },
        {"scan_code": 42, "key_name": "KEY_'\"\\", "date": "2022-01-01"},
        {"scan_code": 44, "key_name": "KEY_\u2022\u00a9\u00ae", "date": "2022-01-01"},
        {"scan_code": 45, "key_name": "MULTI, KEY, COMBO", "date": "2022-01-01"},
    ]

    db_manager.write_to_database(mock_db_path, input_events)

    mock_cursor.executemany.assert_called_once_with(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        expected,
    )
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()
