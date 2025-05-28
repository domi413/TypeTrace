"""Tests to assure data integrity."""

import sqlite3

import pytest

from typetrace.sql import SQLQueries


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Set up an in-memory SQLite database and create the keystrokes table.

    Returns:
        sqlite3.Connection: An in-memory SQLite database connection.

    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(SQLQueries.CREATE_KEYSTROKES_TABLE)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def cursor(db_connection: sqlite3.Connection) -> sqlite3.Cursor:
    """Provide a cursor for the database connection.

    Args:
        db_connection: The SQLite database connection.

    Returns:
        sqlite3.Cursor: A cursor for executing queries.

    """
    return db_connection.cursor()


def test_create_keystrokes_table(cursor: sqlite3.Cursor) -> None:
    """Test that the keystrokes table is created correctly.

    Args:
        cursor: The cursor for executing queries.

    """
    cursor.execute("PRAGMA table_info(keystrokes)")
    columns = cursor.fetchall()
    assert columns[0] == (0, "id", "INTEGER", 0, None, 1)
    assert columns[1] == (1, "scan_code", "INTEGER", 1, None, 0)
    assert columns[2] == (2, "key_name", "TEXT", 1, None, 0)
    assert columns[3] == (3, "date", "DATE", 1, None, 0)
    assert columns[4] == (4, "count", "INTEGER", 0, "0", 0)


def test_insert_or_update_keystroke(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test inserting and updating a keystroke record.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert a new keystroke
    cursor.execute(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        {"scan_code": 1, "key_name": "A", "date": "2025-05-28"},
    )
    db_connection.commit()

    # Verify insertion
    cursor.execute("SELECT scan_code, key_name, date, count FROM keystrokes")
    assert cursor.fetchone() == (1, "A", "2025-05-28", 1)

    # Update the same keystroke (should increment count)
    cursor.execute(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        {"scan_code": 1, "key_name": "A", "date": "2025-05-28"},
    )
    db_connection.commit()

    # Verify update
    cursor.execute("SELECT scan_code, key_name, date, count FROM keystrokes")
    assert cursor.fetchone() == (1, "A", "2025-05-28", 2)


def test_get_all_keystrokes(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving all keystrokes grouped by scan_code and key_name.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query all keystrokes
    cursor.execute(SQLQueries.GET_ALL_KEYSTROKES)
    results = cursor.fetchall()
    expected = [
        (1, 2, "A", "2025-05-27"),
        (2, 1, "B", "2025-05-28"),
    ]
    assert results == expected


def test_get_top_keystrokes_all_time(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving top keystrokes by total count.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query top 1 keystroke
    cursor.execute(SQLQueries.GET_TOP_KEYSTROKES_ALL_TIME, (1,))
    results = cursor.fetchall()
    assert results == [(1, 2, "A", "2025-05-27")]


def test_get_top_keystrokes_by_date(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving top keystrokes for a specific date.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-27"},
            {"scan_code": 3, "key_name": "C", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query top 1 keystroke for 2025-05-27
    cursor.execute(SQLQueries.GET_TOP_KEYSTROKES_BY_DATE, ("2025-05-27", 1))
    results = cursor.fetchall()
    assert results == [(1, 2, "A", "2025-05-27")]


def test_get_total_presses(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving the total number of keystroke presses.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query total presses
    cursor.execute(SQLQueries.GET_TOTAL_PRESSES)
    assert cursor.fetchone()[0] == 3


def test_get_total_keystroke_count_by_date(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving total keystroke count for a specific date.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query total count for 2025-05-27
    cursor.execute(SQLQueries.GET_TOTAL_KEYSTROKE_COUNT_BY_DATE, ("2025-05-27",))
    assert cursor.fetchone()[0] == 2


def test_get_highest_count(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving the highest total count for any key.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query highest count
    cursor.execute(SQLQueries.GET_HIGHEST_COUNT)
    assert cursor.fetchone()[0] == 2


def test_get_keystrokes_by_date(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving all keystrokes for a specific date.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-27"},
            {"scan_code": 3, "key_name": "C", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query keystrokes for 2025-05-27
    cursor.execute(SQLQueries.GET_KEYSTROKES_BY_DATE, ("2025-05-27",))
    results = cursor.fetchall()
    expected = [
        (1, 1, "A", "2025-05-27"),
        (2, 1, "B", "2025-05-27"),
    ]
    assert results == expected


def test_get_daily_keystroke_counts(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test retrieving daily keystroke counts for the last 7 days.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Query daily counts
    cursor.execute(SQLQueries.GET_DAILY_KEYSTROKE_COUNTS)
    results = cursor.fetchall()
    expected = [
        ("2025-05-27", 2),
        ("2025-05-28", 1),
    ]
    assert results == expected


def test_clear_keystrokes(
    db_connection: sqlite3.Connection,
    cursor: sqlite3.Cursor,
) -> None:
    """Test clearing all keystrokes from the table.

    Args:
        db_connection: The SQLite database connection.
        cursor: The cursor for executing queries.

    """
    # Insert sample data
    cursor.executemany(
        SQLQueries.INSERT_OR_UPDATE_KEYSTROKE,
        [
            {"scan_code": 1, "key_name": "A", "date": "2025-05-27"},
            {"scan_code": 2, "key_name": "B", "date": "2025-05-28"},
        ],
    )
    db_connection.commit()

    # Clear the table
    cursor.execute(SQLQueries.CLEAR_KEYSTROKES)
    db_connection.commit()

    # Verify table is empty
    cursor.execute("SELECT COUNT(*) FROM keystrokes")
    assert cursor.fetchone()[0] == 0
