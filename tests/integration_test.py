"""Integration test for simultaneous read/write operations with DatabaseManager."""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from typetrace.backend.db import DatabaseManager


# Fixture for temporary database
@pytest.fixture
def setup_db() -> tuple[Path, DatabaseManager]:
    """Set up a temporary SQLite database for testing.

    Yields:
        tuple: (temp_db_path, db_manager) for test usage.

    """
    temp_db_path = Path("test_temp.db")
    db_manager = DatabaseManager()
    db_manager.initialize_database(temp_db_path)
    yield temp_db_path, db_manager
    if temp_db_path.exists():
        temp_db_path.unlink()


# Test function
def test_simultaneous_read_write_and_compare(
    setup_db: tuple[Path, DatabaseManager],
) -> None:
    """Test simultaneous read and write operations and compare in-memory vs DB values.

    Args:
        setup_db: Fixture providing temp_db_path and db_manager.

    """
    temp_db_path, db_manager = setup_db
    in_memory_keystrokes = []

    # Current timestamp with timezone
    current_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Write thread
    def write_to_db() -> None:
        """Write keystroke events to the database."""
        events = [
            {"scan_code": i, "name": f"key_{i}", "date": current_time}
            for i in range(100)
        ]
        db_manager.write_to_database(temp_db_path, events)
        in_memory_keystrokes.extend([
            {"scan_code": event["scan_code"],
             "key_name": event["name"],
             "date": event["date"]}
            for event in events
        ])

    # Read thread
    def read_from_db() -> list[dict]:
        """Read keystroke events from the database."""
        read_keystrokes = []
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        for _ in range(50):
            cursor.execute("SELECT scan_code, key_name, date FROM keystrokes")
            read_keystrokes.extend(cursor.fetchall())
            import time
            time.sleep(0.01)
        conn.close()
        return [{"scan_code": r[0], "key_name": r[1], "date": r[2]}
                for r in read_keystrokes]

    # Start the threads
    write_thread = threading.Thread(target=write_to_db)
    read_thread = threading.Thread(target=read_from_db)
    write_thread.start()
    read_thread.start()

    # Wait for completion
    write_thread.join()
    read_from_db()
    # Read from database
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT scan_code, key_name, date FROM keystrokes")
    db_keystrokes = cursor.fetchall()
    conn.close()
    db_values = [{"scan_code": r[0], "key_name": r[1], "date": r[2]}
                 for r in db_keystrokes]

    # Comparison
    assert len(in_memory_keystrokes) == len(db_values)
    for mem_val, db_val in zip(
        sorted(in_memory_keystrokes, key=lambda x: x["scan_code"]),
        sorted(db_values, key=lambda x: x["scan_code"]),
    ):
        assert mem_val["scan_code"] == db_val["scan_code"]
        assert mem_val["key_name"] == db_val["key_name"]
        assert mem_val["date"] == db_val["date"]
