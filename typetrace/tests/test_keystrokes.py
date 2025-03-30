import pytest
import sys
from unittest.mock import MagicMock, patch


# Fixture to mock gi.repository for all tests
@pytest.fixture(autouse=True)
def mock_gi(mocker):
    """Mock gi.repository to allow tests to run without PyGObject dependencies."""
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):
        mock_repository.GObject = MagicMock()

        # Mock GObject.Object as a simple class for instantiation
        class MockGObject:
            def __init__(self, *args, **kwargs):
                # Allow attributes to be set directly on the instance
                pass

        mock_repository.GObject.Object = MockGObject
        # Mock GObject.Property as a no-op decorator
        mock_repository.GObject.Property = lambda *args, **kwargs: lambda x: x

        yield mock_repository


# Fixture to mock sqlite3.connect with context manager support
@pytest.fixture
def mock_sqlite3(mocker):
    """Mock sqlite3 connection and cursor for database interactions."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Add context manager support to mock_conn
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_conn.cursor.return_value = mock_cursor

    # Patch sqlite3.connect to return the mock connection
    mocker.patch("sqlite3.connect", return_value=mock_conn)
    return mock_conn, mock_cursor


def test_keystroke_init(mocker, mock_gi):
    """Test the initialization of the Keystroke class."""
    from typetrace.model.keystrokes import Keystroke

    # Create a Keystroke instance
    keystroke = Keystroke(scan_code=16, count=5, key_name="KEY_Q")

    # Verify attributes are set correctly
    assert keystroke.scan_code == 16
    assert keystroke.count == 5
    assert keystroke.key_name == "Q"  # KEY_ prefix should be removed


def test_get_all_keystrokes(mock_sqlite3, mocker, mock_gi):
    """Test retrieving all keystrokes from the database."""
    from typetrace.model.keystrokes import KeystrokeStore

    # Setup mock database response
    mock_conn, mock_cursor = mock_sqlite3
    mock_cursor.fetchall.return_value = [(16, 5, "KEY_Q"), (17, 10, "KEY_W")]

    # Instantiate KeystrokeStore
    store = KeystrokeStore()

    # Call the method
    keystrokes = store.get_all_keystrokes()

    # Verify the results
    assert len(keystrokes) == 2
    assert keystrokes[0].scan_code == 16
    assert keystrokes[0].count == 5
    assert keystrokes[0].key_name == "Q"
    assert keystrokes[1].scan_code == 17
    assert keystrokes[1].count == 10
    assert keystrokes[1].key_name == "W"
    mock_cursor.execute.assert_called_once_with(
        "SELECT scan_code, count, key_name FROM keystrokes"
    )


def test_get_total_presses(mock_sqlite3, mocker, mock_gi):
    """Test calculating the total number of key presses."""
    from typetrace.model.keystrokes import KeystrokeStore

    # Setup mock database response
    mock_conn, mock_cursor = mock_sqlite3
    mock_cursor.fetchone.return_value = [15]  # Total presses

    # Instantiate KeystrokeStore
    store = KeystrokeStore()

    # Call the method
    total = store.get_total_presses()

    # Verify the result
    assert total == 15
    mock_cursor.execute.assert_called_once_with("SELECT SUM(count) FROM keystrokes")


def test_get_highest_count(mock_sqlite3, mocker, mock_gi):
    """Test retrieving the highest keystroke count."""
    from typetrace.model.keystrokes import KeystrokeStore

    # Setup mock database response
    mock_conn, mock_cursor = mock_sqlite3
    mock_cursor.fetchone.return_value = [20]  # Highest count

    # Instantiate KeystrokeStore
    store = KeystrokeStore()

    # Call the method
    highest = store.get_highest_count()

    # Verify the result
    assert highest == 20
    mock_cursor.execute.assert_called_once_with("SELECT MAX(count) FROM keystrokes")


def test_clear_success(mock_sqlite3, mocker, mock_gi):
    """Test clearing all keystrokes from the database successfully."""
    from typetrace.model.keystrokes import KeystrokeStore

    # Setup mock database response
    mock_conn, mock_cursor = mock_sqlite3
    mock_conn.commit = mocker.Mock()  # Mock commit to simulate success

    # Instantiate KeystrokeStore
    store = KeystrokeStore()

    # Call the method
    result = store.clear()

    # Verify the result
    assert result is True
    mock_cursor.execute.assert_called_once_with("DELETE FROM keystrokes")
    mock_conn.commit.assert_called_once()
