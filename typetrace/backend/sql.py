"""SQL queries for TypeTrace database operations."""

from typing import final


@final
class SQLQueries:
    """SQL queries for TypeTrace database operations."""

    def __init__(self) -> None:
        """Private constructor to prevent instantiation."""
        raise TypeError

    BEGIN_TRANSACTION = "BEGIN TRANSACTION"

    CREATE_KEYSTROKE_TABLE = """
    CREATE TABLE IF NOT EXISTS keystrokes (
        keystroke_id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_name TEXT NOT NULL UNIQUE
    );
    """

    CREATE_KEYSTROKE_LOGS_TABLE = """
    CREATE TABLE IF NOT EXISTS keystroke_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        keystroke_id INTEGER NOT NULL,
        key_count INTEGER NOT NULL DEFAULT 0,
        log_date DATE NOT NULL,
        FOREIGN KEY (keystroke_id) REFERENCES keystrokes(keystroke_id) ON DELETE CASCADE,
        UNIQUE(keystroke_id, log_date)
    );
    """

    INSERT_KEYSTROKE = """
    INSERT OR IGNORE INTO keystrokes (key_name)
    VALUES (:key_name)
    """

    GET_KEYSTROKE_ID = """
    SELECT keystroke_id FROM keystrokes WHERE key_name = :key_name
    """

    INSERT_OR_UPDATE_KEYSTROKE_LOG = """
    INSERT INTO keystroke_logs (keystroke_id, key_count, log_date)
    VALUES (:keystroke_id, 1, date('now'))
    ON CONFLICT(keystroke_id, log_date) DO UPDATE SET
        key_count = key_count + 1
    """

    # TODO: create index for tables
