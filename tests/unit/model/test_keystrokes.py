import pytest
from unittest.mock import MagicMock, patch
import sqlite3

from keystrokes import Keystroke, KeystrokeStore
from typetrace.config import DatabasePath


class TestKeystroke:
    """Test suite for Keystroke class."""

    def test_keystroke_initialization(self):
        """Test initialization of Keystroke object."""
        keystroke = Keystroke(scan_code=42, count=10, key_name="KEY_A")
        assert keystroke.scan_code == 42
        assert keystroke.count == 10
        assert keystroke.key_name == "A"  # KEY_ prefix removed

    def test_keystroke_default_properties(self):
        """Test default GObject properties of Keystroke."""
        keystroke = Keystroke(scan_code=0, count=0, key_name="")
        assert keystroke.get_property("scan_code") == 0
        assert keystroke.get_property("count") == 0
        assert keystroke.get_property("key_name") == ""

    def test_keystroke_key_name_no_prefix(self):
        """Test key_name processing when no KEY_ prefix exists."""
        keystroke = Keystroke(scan_code=1, count=5, key_name="ENTER")
        assert keystroke.key_name == "ENTER"


class TestKeystrokeStore:
    """Test suite for KeystrokeStore class."""

    @pytest.fixture
    def keystroke_store(self):
        """Provide a KeystrokeStore instance with mocked database path."""
        with patch.object(DatabasePath, "DB_PATH", "~/.local/share/typetrace/TypeTrace.db"):
            return KeystrokeStore()

    @pytest.fixture
    def mock_sqlite_connect(self):
        """Mock sqlite3.connect to simulate database behavior."""
        with patch("sqlite3.connect") as mock_connect:
            yield mock_connect

    def test_initialization(self):
        """Test KeystrokeStore initialization."""
        keystroke_store = KeystrokeStore()
        assert str(keystroke_store.db_path) == str(DatabasePath.DB_PATH)

    def test_get_all_keystrokes_success(self, keystroke_store, mock_sqlite_connect):
        """Test retrieving all keystrokes successfully."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 10, "KEY_A"),
            (2, 5, "KEY_B"),
        ]
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        keystrokes = keystroke_store.get_all_keystrokes()
        assert len(keystrokes) == 2
        assert isinstance(keystrokes[0], Keystroke)
        assert keystrokes[0].scan_code == 1
        assert keystrokes[0].count == 10
        assert keystrokes[0].key_name == "A"
        assert keystrokes[1].scan_code == 2
        assert keystrokes[1].count == 5
        assert keystrokes[1].key_name == "B"
        mock_cursor.execute.assert_called_with("SELECT scan_code, count, key_name FROM keystrokes")

    def test_get_all_keystrokes_empty(self, keystroke_store, mock_sqlite_connect):
        """Test retrieving keystrokes from an empty database."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        keystrokes = keystroke_store.get_all_keystrokes()
        assert len(keystrokes) == 0
        mock_cursor.execute.assert_called_with("SELECT scan_code, count, key_name FROM keystrokes")

    def test_get_all_keystrokes_db_error(self, keystroke_store, mock_sqlite_connect):
        """Test handling of database errors in get_all_keystrokes."""
        mock_sqlite_connect.side_effect = sqlite3.Error
        keystrokes = keystroke_store.get_all_keystrokes()
        assert len(keystrokes) == 0

    def test_get_total_presses_success(self, keystroke_store, mock_sqlite_connect):
        """Test retrieving total key presses successfully."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (100,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        total = keystroke_store.get_total_presses()
        assert total == 100
        mock_cursor.execute.assert_called_with("SELECT SUM(count) FROM keystrokes")

    def test_get_total_presses_empty(self, keystroke_store, mock_sqlite_connect):
        """Test total presses when database is empty or no counts."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        total = keystroke_store.get_total_presses()
        assert total == 0
        mock_cursor.execute.assert_called_with("SELECT SUM(count) FROM keystrokes")

    def test_get_total_presses_db_error(self, keystroke_store, mock_sqlite_connect):
        """Test handling of database errors in get_total_presses."""
        mock_sqlite_connect.side_effect = sqlite3.Error
        total = keystroke_store.get_total_presses()
        assert total == 0

    def test_get_highest_count_success(self, keystroke_store, mock_sqlite_connect):
        """Test retrieving the highest keystroke count successfully."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (50,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        highest = keystroke_store.get_highest_count()
        assert highest == 50
        mock_cursor.execute.assert_called_with("SELECT MAX(count) FROM keystrokes")

    def test_get_highest_count_empty(self, keystroke_store, mock_sqlite_connect):
        """Test highest count when database is empty."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        highest = keystroke_store.get_highest_count()
        assert highest == 0
        mock_cursor.execute.assert_called_with("SELECT MAX(count) FROM keystrokes")

    def test_get_highest_count_db_error(self, keystroke_store, mock_sqlite_connect):
        """Test handling of database errors in get_highest_count."""
        mock_sqlite_connect.side_effect = sqlite3.Error
        highest = keystroke_store.get_highest_count()
        assert highest == 0

    def test_clear_success(self, keystroke_store, mock_sqlite_connect):
        """Test clearing the keystrokes table successfully."""
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_sqlite_connect.return_value.__enter__.return_value = mock_connection

        result = keystroke_store.clear()
        assert result is True
        mock_cursor.execute.assert_called_with("DELETE FROM keystrokes")
        mock_connection.commit.assert_called_once()

    def test_clear_db_error(self, keystroke_store, mock_sqlite_connect):
        """Test handling of database errors in clear."""
        mock_sqlite_connect.side_effect = sqlite3.Error
        result = keystroke_store.clear()
        assert result is False