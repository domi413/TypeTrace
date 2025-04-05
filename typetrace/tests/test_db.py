"""Unit tests for the database module."""

import sqlite3
from pathlib import Path

import pytest
from typetrace.backend.db import (
    get_db_connection,
    initialize_database,
    update_keystroke_counts,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary database file for testing.

    Args:
        tmp_path: Temporary path provided by pytest.

    """
    return tmp_path / "test.db"


def test_get_db_connection(temp_db: Path) -> None:
    """Test that get_db_connection returns a valid SQLite connection."""
    with get_db_connection(temp_db) as conn:
        assert isinstance(conn, sqlite3.Connection)
        cursor = conn.cursor()
        cursor.execute("SELECT sqlite_version();")
        assert cursor.fetchone()[0]


def test_initialize_database(temp_db: Path) -> None:
    """Test that initialize_database creates the keystrokes table."""
    initialize_database(temp_db)
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='keystrokes';"
        )
        assert cursor.fetchone() is not None


def test_update_keystroke_counts(temp_db: Path) -> None:
    """Test that update_keystroke_counts adds a single key event correctly."""
    initialize_database(temp_db)
    events = [{"scan_code": 1, "name": "a"}]
    update_keystroke_counts(temp_db, events)
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key_name, count FROM keystrokes WHERE scan_code=1")
        key_name, count = cursor.fetchone()
        assert key_name == "a"
        assert count == 1


def test_update_keystroke_counts_empty(temp_db: Path) -> None:
    """Test that update_keystroke_counts handles an empty event list."""
    initialize_database(temp_db)
    update_keystroke_counts(temp_db, [])
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keystrokes")
        assert cursor.fetchone()[0] == 0


def test_update_keystroke_counts_tuple(temp_db: Path) -> None:
    """Test that update_keystroke_counts handles tuple key names correctly."""
    initialize_database(temp_db)
    events = [{"scan_code": 2, "name": ("shift", "a")}]
    update_keystroke_counts(temp_db, events)
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key_name, count FROM keystrokes WHERE scan_code=2")
        key_name, count = cursor.fetchone()
        assert key_name == "shift, a"
        assert count == 1
