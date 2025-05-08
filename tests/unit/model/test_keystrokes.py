"""Unit tests for basic keystroke database operations using SQLite."""

import sqlite3
import unittest

# Constants for test data
SCAN_CODE_A = 65
SCAN_CODE_B = 66
SCAN_CODE_C = 67
SCAN_CODE_G = 71
EXPECTED_COUNT = 1
EXPECTED_HIGHEST_COUNT = 2
EXPECTED_ROW_COUNT = 2


class TestKeystrokeDatabase(unittest.TestCase):
    """Unit tests for basic keystroke database operations using SQLite."""

    def setUp(self) -> None:
        """Set up an in-memory SQLite database and create the keystrokes table."""
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE keystrokes (
                scan_code INTEGER,
                key_char TEXT,
                count INTEGER
            )
        """)

    def tearDown(self) -> None:
        """Close the SQLite connection after each test."""
        self.conn.close()

    def test_insert_single_keystroke(self) -> None:
        """Test inserting a single keystroke entry into the database."""
        self.cursor.execute(
            "INSERT INTO keystrokes (scan_code, key_char, count) VALUES (?, ?, ?)",
            (SCAN_CODE_A, "A", 1),
        )
        self.conn.commit()
        self.cursor.execute(
            "SELECT * FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_A,),
        )
        row = self.cursor.fetchone()

        assert row is not None
        assert row[0] == SCAN_CODE_A
        assert row[1] == "A"
        assert row[2] == 1

    def test_insert_multiple_keystrokes(self) -> None:
        """Test inserting multiple keystroke entries into the database."""
        self.cursor.executemany(
            "INSERT INTO keystrokes (scan_code, key_char, count) VALUES (?, ?, ?)",
            [(SCAN_CODE_B, "B", 1), (SCAN_CODE_A, "A", 1)],
        )
        self.conn.commit()

        self.cursor.execute(
            "SELECT * FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_B,),
        )
        row_b = self.cursor.fetchone()
        assert row_b == (SCAN_CODE_B, "B", 1)

        self.cursor.execute(
            "SELECT * FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_A,),
        )
        row_a = self.cursor.fetchone()
        assert row_a == (SCAN_CODE_A, "A", 1)

    def test_delete_keystroke(self) -> None:
        """Test deleting a keystroke entry from the database."""
        self.cursor.execute(
            "INSERT INTO keystrokes (scan_code, key_char, count) VALUES (?, ?, ?)",
            (SCAN_CODE_C, "C", 1),
        )
        self.conn.commit()
        self.cursor.execute(
            "DELETE FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_C,),
        )
        self.conn.commit()

        self.cursor.execute(
            "SELECT * FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_C,),
        )
        row = self.cursor.fetchone()
        assert row is None

    def test_get_all_keystrokes(self) -> None:
        """Test retrieving all keystrokes from the database."""
        self.cursor.executemany(
            "INSERT INTO keystrokes (scan_code, key_char, count) VALUES (?, ?, ?)",
            [(SCAN_CODE_A, "A", 1), (SCAN_CODE_B, "B", 1)],
        )
        self.conn.commit()
        self.cursor.execute("SELECT * FROM keystrokes")
        rows = self.cursor.fetchall()

        assert len(rows) == EXPECTED_ROW_COUNT
        assert ("A",) in [(row[1],) for row in rows]
        assert ("B",) in [(row[1],) for row in rows]

    def test_get_highest_count(self) -> None:
        """Test retrieving the keystroke with the highest count."""
        self.cursor.executemany(
            "INSERT INTO keystrokes (scan_code, key_char, count) VALUES (?, ?, ?)",
            [
                (SCAN_CODE_G, "G", EXPECTED_COUNT),
                (SCAN_CODE_A, "A", EXPECTED_HIGHEST_COUNT),
            ],
        )
        self.conn.commit()

        self.cursor.execute(
            "SELECT * FROM keystrokes WHERE scan_code = ?",
            (SCAN_CODE_A,),
        )
        row = self.cursor.fetchone()

        assert row is not None
        assert row[0] == SCAN_CODE_A
        assert row[1] == "A"
        assert row[2] == EXPECTED_HIGHEST_COUNT


if __name__ == "__main__":
    unittest.main()
