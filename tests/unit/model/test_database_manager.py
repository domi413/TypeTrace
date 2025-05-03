"""Unit tests for the DatabaseManager class in typetrace.backend.db."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from typetrace.backend.db import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test suite for the DatabaseManager class."""

    def setUp(self):
        """Create a temporary file path for each test."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test.db"
        self.db_manager = DatabaseManager()

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        self.tmp_dir.cleanup()

    def test_initialize_database_success(self):
        """Test that initialize_database creates the keystrokes table."""
        self.db_manager.initialize_database(self.db_path)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='keystrokes'",
        )
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result, "Keystrokes table should exist")
        self.assertEqual(result[0], "keystrokes")

    def test_write_to_database_success(self):
        """Test that write_to_database inserts events into the database."""
        self.db_manager.initialize_database(self.db_path)

        events = [{"scan_code": 16, "name": "q", "date": "2025-04-21"}]
        self.db_manager.write_to_database(self.db_path, events)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT scan_code, key_name, date FROM keystrokes "
            "WHERE scan_code = 16",
        )
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result, "Event should be inserted")
        self.assertEqual(result, (16, "q", "2025-04-21"))

    def test_write_to_database_empty_events(self):
        """Test that write_to_database handles an empty events list."""
        self.db_manager.initialize_database(self.db_path)

        events = []
        self.db_manager.write_to_database(self.db_path, events)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keystrokes")
        result = cursor.fetchone()
        conn.close()

        self.assertEqual(result[0], 0, "No events should be inserted")
