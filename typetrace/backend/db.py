"""Database operations for TypeTrace."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List


class DatabaseManager:
    @staticmethod
    @contextmanager
    def get_db_connection(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def initialize_database(db_path: Path) -> None:
        with DatabaseManager.get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS keystrokes (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                keycode TEXT NOT NULL,
                                timestamp REAL NOT NULL
                            )""")
            conn.commit()

    @staticmethod
    def update_keystroke_counts(db_path: Path, events: List[KeyEvent]) -> None:
        with DatabaseManager.get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """INSERT INTO keystrokes (keycode, timestamp)
                                  VALUES (:keycode, :timestamp)""",
                events,
            )
            conn.commit()

    @staticmethod
    def write_to_database(db_path: Path, events: List[KeyEvent]) -> None:
        DatabaseManager.update_keystroke_counts(db_path, events)
