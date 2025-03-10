"""SQL commands for TypeTrace database operations."""

from __future__ import annotations

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

BEGIN_TRANSACTION = "BEGIN TRANSACTION"
