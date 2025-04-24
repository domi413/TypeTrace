import sqlite3

from typetrace.backend.db import DatabaseManager


class TestDatabaseManager:
    """Test suite for the DatabaseManager class with minimal tests."""

    def test_initialize_database_success(self, tmp_path):
        """Test that initialize_database creates the keystrokes table."""
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager()
        db_manager.initialize_database(db_path)

        # Check if the table was created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='keystrokes'",
        )
        result = cursor.fetchone()
        assert result is not None, "Keystrokes table should exist"
        assert result[0] == "keystrokes"
        conn.close()

    def test_write_to_database_success(self, tmp_path):
        """Test that write_to_database inserts events into the database."""
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager()

        # Create the table first
        db_manager.initialize_database(db_path)

        # Sample event
        events = [{"scan_code": 16, "name": "q", "date": "2025-04-21"}]

        # Write the event to the database
        db_manager.write_to_database(db_path, events)

        # Check if the event was inserted
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT scan_code, key_name, date FROM keystrokes WHERE scan_code = 16",
        )
        result = cursor.fetchone()
        assert result is not None, "Event should be inserted"
        assert result == (16, "q", "2025-04-21"), "Event data should match"
        conn.close()

    def test_write_to_database_empty_events(self, tmp_path):
        """Test that write_to_database handles an empty events list."""
        db_path = tmp_path / "test.db"
        db_manager = DatabaseManager()

        # Create the table first
        db_manager.initialize_database(db_path)

        # Write an empty list of events
        events = []
        db_manager.write_to_database(db_path, events)

        # Check that the database is empty
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keystrokes")
        result = cursor.fetchone()
        assert result[0] == 0, "No events should be inserted"
        conn.close()
