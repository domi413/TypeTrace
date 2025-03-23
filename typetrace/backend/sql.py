"""SQL queries for TypeTrace database operations."""

from typing import final


@final
class SQLQueries:
    """SQL queries for TypeTrace database operations."""

    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS keystrokes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keycode TEXT NOT NULL,
        timestamp REAL NOT NULL
    )
    """

    CREATE_KEYSTROKES_TABLE = """
    CREATE TABLE IF NOT EXISTS keystrokes (
        scan_code INTEGER PRIMARY KEY,
        count INTEGER DEFAULT 0,
        key_name TEXT
    )
    """

    INSERT_OR_UPDATE_KEYSTROKE = """
    INSERT INTO keystrokes (scan_code, count, key_name)
    VALUES (?, 1, ?)
    ON CONFLICT(scan_code) DO UPDATE SET
        count = count + 1,
        key_name = ?
    """

    INSERT_KEYSTROKE = """
    INSERT INTO keystrokes (keycode, timestamp)
    VALUES (:keycode, :timestamp)
    """

    BEGIN_TRANSACTION = "BEGIN TRANSACTION"
