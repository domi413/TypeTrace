"""Tests for the KeystrokeStore class."""
from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from typetrace.frontend.model.keystrokes import Keystroke, KeystrokeStore
from typetrace.sql import SQLQueries

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


@pytest.fixture
def mock_conn(mocker: MockerFixture) -> Mock:
    """Provide a mock SQLite connection."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def keystroke_store(mock_conn: Mock) -> KeystrokeStore:
    """Provide a KeystrokeStore instance for testing."""
    return KeystrokeStore(mock_conn)


# =============================================================================
# =================== Tests for get_all_keystrokes method =====================
# =============================================================================
def test_get_all_keystrokes(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving all keystrokes."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (30, 100, "KEY_A", "2022-01-01"),
        (42, 50, "KEY_LEFTSHIFT", "2022-01-01"),
    ]

    result = keystroke_store.get_all_keystrokes()

    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_ALL_KEYSTROKES)
    assert len(result) == 2
    assert isinstance(result[0], Keystroke)
    assert result[0].scan_code == 30
    assert result[0].count == 100
    assert result[0].key_name == "A"
    assert result[0].date == "2022-01-01"


def test_get_all_keystrokes_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_all_keystrokes handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_all_keystrokes()

    assert result == []
    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_ALL_KEYSTROKES)


# =============================================================================
# ==================== Tests for get_total_presses method =====================
# =============================================================================
def test_get_total_presses(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving total key presses."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = (1000,)

    result = keystroke_store.get_total_presses()

    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_TOTAL_PRESSES)
    assert result == 1000


def test_get_total_presses_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_total_presses handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_total_presses()

    assert result == 0
    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_TOTAL_PRESSES)


# =============================================================================
# ==================== Tests for get_highest_count method =====================
# =============================================================================
def test_get_highest_count(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving highest keystroke count."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = (500,)

    result = keystroke_store.get_highest_count()

    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_HIGHEST_COUNT)
    assert result == 500


def test_get_highest_count_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_highest_count handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_highest_count()

    assert result == 0
    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_HIGHEST_COUNT)


# =============================================================================
# ================== Tests for get_keystrokes_by_date method ==================
# =============================================================================
def test_get_keystrokes_by_date(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving keystrokes for a specific date."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (30, 100, "KEY_A", "2022-01-01"),
    ]

    result = keystroke_store.get_keystrokes_by_date("2022-01-01")

    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_KEYSTROKES_BY_DATE,
        ("2022-01-01",),
    )
    assert len(result) == 1
    assert result[0].key_name == "A"


def test_get_keystrokes_by_date_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_keystrokes_by_date handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_keystrokes_by_date("2022-01-01")

    assert result == []
    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_KEYSTROKES_BY_DATE,
        ("2022-01-01",),
    )


# =============================================================================
# ==================== Tests for get_top_keystrokes method ====================
# =============================================================================
def test_get_top_keystrokes_all_time(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving top keystrokes without date filter."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (30, 100, "KEY_A", "2022-01-01"),
        (42, 50, "KEY_LEFTSHIFT", "2022-01-01"),
    ]

    result = keystroke_store.get_top_keystrokes(limit=2)

    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_TOP_KEYSTROKES_ALL_TIME,
        (2,),
    )
    assert len(result) == 2
    assert result[0].count == 100


def test_get_top_keystrokes_by_date(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving top keystrokes for a specific date."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        (30, 100, "KEY_A", "2022-01-01"),
    ]

    result = keystroke_store.get_top_keystrokes(limit=1, date="2022-01-01")

    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_TOP_KEYSTROKES_BY_DATE,
        ("2022-01-01", 1),
    )
    assert len(result) == 1


def test_get_top_keystrokes_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_top_keystrokes handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_top_keystrokes(limit=2)

    assert result == []
    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_TOP_KEYSTROKES_ALL_TIME,
        (2,),
    )


# =============================================================================
# ================ Tests for get_total_keystroke_count method =================
# =============================================================================
def test_get_total_keystroke_count_all_time(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving total keystroke count without date filter."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = (1000,)

    result = keystroke_store.get_total_keystroke_count()

    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_TOTAL_PRESSES)
    assert result == 1000


def test_get_total_keystroke_count_by_date(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving total keystroke count for a specific date."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchone.return_value = (500,)

    result = keystroke_store.get_total_keystroke_count(date="2022-01-01")

    mock_cursor.execute.assert_called_once_with(
        SQLQueries.GET_TOTAL_KEYSTROKE_COUNT_BY_DATE,
        ("2022-01-01",),
    )
    assert result == 500


def test_get_total_keystroke_count_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_total_keystroke_count handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_total_keystroke_count()

    assert result == 0
    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_TOTAL_PRESSES)


# =============================================================================
# ========================= Tests for clear method ============================
# =============================================================================
def test_clear(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
    mocker: MockerFixture,
) -> None:
    """Test clearing all keystrokes."""
    mock_cursor = mock_conn.cursor.return_value
    mock_emit = mocker.spy(keystroke_store, "emit")

    result = keystroke_store.clear()

    mock_cursor.execute.assert_called_once_with(SQLQueries.CLEAR_KEYSTROKES)
    mock_conn.commit.assert_called_once()
    mock_emit.assert_called_once_with("changed")
    assert result is True


def test_clear_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test clear handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.clear()

    assert result is False
    mock_cursor.execute.assert_called_once_with(SQLQueries.CLEAR_KEYSTROKES)


# =============================================================================
# ================ Tests for get_daily_keystroke_counts method ================
# =============================================================================
def test_get_daily_keystroke_counts(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test retrieving daily keystroke counts."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.return_value = [
        ("2022-01-01", 100),
        ("2022-01-02", 200),
    ]

    result = keystroke_store.get_daily_keystroke_counts()

    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_DAILY_KEYSTROKE_COUNTS)
    assert len(result) == 2
    assert result[0]["date"] == "2022-01-01"
    assert result[0]["count"] == 100


def test_get_daily_keystroke_counts_handles_error(
    keystroke_store: KeystrokeStore,
    mock_conn: Mock,
) -> None:
    """Test get_daily_keystroke_counts handles SQLite errors."""
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.side_effect = sqlite3.Error("Mock SQLite error")

    result = keystroke_store.get_daily_keystroke_counts()

    assert result == []
    mock_cursor.execute.assert_called_once_with(SQLQueries.GET_DAILY_KEYSTROKE_COUNTS)
