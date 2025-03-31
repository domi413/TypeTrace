"""Unit-tests for the keystrokes model."""

import sqlite3
from unittest.mock import patch

import pytest

from typetrace.model.keystrokes import Keystroke, KeystrokeStore


# --- Tests for Keystroke Class ---

def test_keystroke_initialization():
    """Test that Keystroke initializes correctly and removes 'KEY_' prefix."""
    ks = Keystroke(42, 10, "KEY_ENTER")
    assert ks.scan_code == 42
    assert ks.count == 10
    assert ks.key_name == "ENTER"


def test_keystroke_key_name_no_prefix():
    """Test that Keystroke leaves key_name unchanged if it doesn't start with 'KEY_'."""
    ks = Keystroke(13, 5, "SHIFT")
    assert ks.key_name == "SHIFT"


# --- Fixture for KeystrokeStore Tests ---

@pytest.fixture
def db_connection():
    """Provide an in-memory SQLite database with a keystrokes table."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE keystrokes (scan_code INTEGER, count INTEGER, key_name TEXT)"
    )
    conn.commit()
    yield conn
    conn.close()


# --- Tests for KeystrokeStore Class ---

def test_get_all_keystrokes(db_connection):
    """Test retrieving all keystrokes from the database."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        cursor = db_connection.cursor()
        cursor.executemany(
            "INSERT INTO keystrokes (scan_code, count, key_name) VALUES (?, ?, ?)",
            [(1, 5, "KEY_A"), (2, 3, "KEY_B")],
        )
        db_connection.commit()
        keystrokes = store.get_all_keystrokes()
        assert len(keystrokes) == 2
        assert keystrokes[0].scan_code == 1
        assert keystrokes[0].count == 5
        assert keystrokes[0].key_name == "A"
        assert keystrokes[1].scan_code == 2
        assert keystrokes[1].count == 3
        assert keystrokes[1].key_name == "B"

def test_get_all_keystrokes_empty(db_connection):
    """Test retrieving keystrokes from an empty database."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        keystrokes = store.get_all_keystrokes()
        assert keystrokes == []

def test_get_total_presses(db_connection):
    """Test calculating the total number of key presses."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        cursor = db_connection.cursor()
        cursor.executemany(
            "INSERT INTO keystrokes (scan_code, count, key_name) VALUES (?, ?, ?)",
            [(1, 5, "KEY_A"), (2, 3, "KEY_B"), (3, 8, "KEY_C")],
        )
        db_connection.commit()
        total = store.get_total_presses()
        assert total == 16  # 5 + 3 + 8

def test_get_total_presses_empty(db_connection):
    """Test total presses calculation with an empty database."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        total = store.get_total_presses()
        assert total == 0

def test_get_highest_count(db_connection):
    """Test retrieving the highest keystroke count."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        cursor = db_connection.cursor()
        cursor.executemany(
            "INSERT INTO keystrokes (scan_code, count, key_name) VALUES (?, ?, ?)",
            [(1, 5, "KEY_A"), (2, 3, "KEY_B"), (3, 8, "KEY_C")],
        )
        db_connection.commit()
        highest = store.get_highest_count()
        assert highest == 8

def test_get_highest_count_empty(db_connection):
    """Test highest count with an empty database."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        highest = store.get_highest_count()
        assert highest == 0

def test_clear(db_connection):
    """Test clearing all keystrokes from the database."""
    store = KeystrokeStore()
    with patch("sqlite3.connect", return_value=db_connection):
        cursor = db_connection.cursor()
        cursor.executemany(
            "INSERT INTO keystrokes (scan_code, count, key_name) VALUES (?, ?, ?)",
            [(1, 5, "KEY_A")],
        )
        db_connection.commit()
        result = store.clear()
        assert result is True
        keystrokes = store.get_all_keystrokes()
        assert keystrokes == []
