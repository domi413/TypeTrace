import sqlite3
from unittest.mock import patch

import pytest

from typetrace.backend.db import DatabaseManager
from typetrace.config import DatabasePath
from typetrace.model.keystrokes import Keystroke, KeystrokeStore


class TestKeystroke:
    """Test suite for the Keystroke class."""

    def test_initialization(self):
        """Test initialization of a Keystroke object."""
        keystroke = Keystroke(scan_code=42, count=10, key_name="KEY_A", date="")
        assert keystroke.scan_code == 42, "Scan code should be set correctly"
        assert keystroke.count == 10, "Count should be set correctly"
        assert keystroke.key_name == "A", "Key name should have the KEY_ prefix removed"
        assert keystroke.date == "", "Date should be set correctly"

    def test_key_name_no_prefix(self):
        """Test key_name processing when no KEY_ prefix exists."""
        keystroke = Keystroke(scan_code=1, count=5, key_name="ENTER", date="")
        assert keystroke.key_name == "ENTER", (
            "Key name should remain unchanged if no KEY_ prefix"
        )


class TestKeystrokeStore:
    """Test suite for the KeystrokeStore class with minimal tests."""

    @pytest.fixture
    def setup_database(self, tmp_path):
        """Set up a temporary database with a keystrokes table compatible with the implementation."""
        db_path = tmp_path / "test.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            # Create a table definition matching the add method
            cursor.execute(
                """
                CREATE TABLE keystrokes (
                    scan_code INTEGER NOT NULL,
                    key_name TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    UNIQUE(scan_code)
                )
                """
            )
            conn.commit()

        # Debug: Print the table definition
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='keystrokes'"
            )
            table_definition = cursor.fetchone()
            print(f"\nKeystrokes table definition:\n{table_definition[0]}\n")

        return db_path

    @pytest.fixture
    def keystroke_store(self, setup_database):
        """Provide a KeystrokeStore instance with a temporary database path."""
        with patch.object(DatabasePath, "DB_PATH", str(setup_database)):
            store = KeystrokeStore()
            return store

    def test_add_success(self, keystroke_store, setup_database):
        """Test adding a keystroke event successfully."""
        event = {
            "key": "KEY_A",
            "scan_code": 30,  # Scan code for 'A'
        }
        result = keystroke_store.add(event)
        assert result is True, "Adding keystroke should succeed"

        # Check if the entry is in the database
        with sqlite3.connect(str(setup_database)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT scan_code, key_name, count FROM keystrokes WHERE scan_code = 30"
            )
            row = cursor.fetchone()
            assert row == (30, "KEY_A", 1), "Keystroke should be inserted with count 1"

    def test_add_mouse_event_ignored(self, keystroke_store, setup_database):
        """Test that mouse events are ignored by the add method."""
        event = {"key": "BTN_LEFT", "scan_code": 272}
        result = keystroke_store.add(event)
        assert result is True, "Adding should succeed even if event is ignored"

        # Check that no entry was added
        with sqlite3.connect(str(setup_database)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM keystrokes")
            count = cursor.fetchone()[0]
            assert count == 0, "Mouse event should not be added to the database"

    def test_get_all_keystrokes_success(self, keystroke_store, setup_database):
        """Test retrieving all keystrokes from the database."""
        # Add an entry
        event = {"key": "KEY_A", "scan_code": 30}
        keystroke_store.add(event)

        keystrokes = keystroke_store.get_all_keystrokes()
        assert len(keystrokes) == 1, "Should retrieve one keystroke"
        assert isinstance(keystrokes[0], Keystroke), "Should return Keystroke objects"
        assert keystrokes[0].scan_code == 30, "Scan code should match"
        assert keystrokes[0].count == 1, "Count should match"
        assert keystrokes[0].key_name == "A", "Key name should have KEY_ prefix removed"
        assert keystrokes[0].date == "", "Date should be empty as it's not used"

    def test_get_all_keystrokes_empty(self, keystroke_store):
        """Test retrieving keystrokes from an empty database."""
        keystrokes = keystroke_store.get_all_keystrokes()
        assert len(keystrokes) == 0, "Should return an empty list for empty database"

    def test_get_highest_count_success(self, keystroke_store, setup_database):
        """Test retrieving the highest count from the database."""
        # Add two entries
        event1 = {"key": "KEY_A", "scan_code": 30}
        event2 = {"key": "KEY_B", "scan_code": 48}
        keystroke_store.add(event1)
        keystroke_store.add(event1)  # Count for KEY_A becomes 2
        keystroke_store.add(event2)  # Count for KEY_B is 1

        highest = keystroke_store.get_highest_count()
        assert highest == 2, "Highest count should be 2"

    def test_get_highest_count_empty(self, keystroke_store):
        """Test highest count when the database is empty."""
        highest = keystroke_store.get_highest_count()
        assert highest == 0, "Should return 0 for an empty database"

    def test_clear_success(self, keystroke_store, setup_database):
        """Test clearing the keystrokes table."""
        # Add an entry
        event = {"key": "KEY_A", "scan_code": 30}
        keystroke_store.add(event)

        # Clear the table
        result = keystroke_store.clear()
        assert result is True, "Clearing should succeed"

        # Check that the table is empty
        with sqlite3.connect(str(setup_database)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM keystrokes")
            count = cursor.fetchone()[0]
            assert count == 0, "Table should be empty after clear"
