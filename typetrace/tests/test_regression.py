from pathlib import Path
import sqlite3
from typetrace.backend.db import (
    initialize_database,
    update_keystroke_counts,
)


def test_update_keystroke_counts(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    events = [{"scan_code": 1, "name": "a"}]
    update_keystroke_counts(db_path, events)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key_name, count FROM keystrokes WHERE scan_code=1")
        key_name, count = cursor.fetchone()
        assert key_name == "a"
        assert count == 1
