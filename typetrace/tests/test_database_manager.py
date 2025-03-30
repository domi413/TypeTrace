import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


# Fixture to mock dependencies
@pytest.fixture(autouse=True)
def mock_dependencies(mocker):
    """Mock shutil and Path for all tests."""
    mock_shutil = MagicMock()
    mock_pathlib = MagicMock()
    with patch.dict(
        "sys.modules",
        {
            "shutil": mock_shutil,
            "pathlib": mock_pathlib,
        },
    ):
        # Mock Path to return a mock object when called
        mock_path = MagicMock()
        mock_pathlib.Path.return_value = mock_path
        mock_path.parent = MagicMock()
        yield mock_shutil, mock_path


def test_export_database_success(mocker, mock_dependencies):
    """Test export_database with a successful export."""
    from typetrace.model.database_manager import DatabaseManager

    mock_shutil, mock_path = mock_dependencies

    # Create DatabaseManager instance
    db_manager = DatabaseManager()
    dest_path = Path("/tmp/export.db")

    # Mock successful copy
    mock_shutil.copy2.return_value = None  # copy2 returns None on success

    # Call the method
    result = db_manager.export_database(dest_path)

    # Verify behavior
    assert result is True
    mock_shutil.copy2.assert_called_once_with(mock_path, dest_path)
    mock_shutil.copy2.side_effect = None  # Ensure no exception was raised


def test_export_database_failure(mocker, mock_dependencies):
    """Test export_database when the export fails."""
    from typetrace.model.database_manager import DatabaseManager

    mock_shutil, mock_path = mock_dependencies

    # Create DatabaseManager instance
    db_manager = DatabaseManager()
    dest_path = Path("/tmp/export.db")

    # Mock failure with an OSError
    mock_shutil.copy2.side_effect = OSError("Permission denied")

    # Call the method
    with patch("builtins.print") as mock_print:
        result = db_manager.export_database(dest_path)

    # Verify behavior
    assert result is False
    mock_shutil.copy2.assert_called_once_with(mock_path, dest_path)
    mock_print.assert_called_once_with("Export failed: Permission denied")


def test_import_database_success(mocker, mock_dependencies):
    """Test import_database with a successful import."""
    from typetrace.model.database_manager import DatabaseManager

    mock_shutil, mock_path = mock_dependencies

    # Create DatabaseManager instance
    db_manager = DatabaseManager()
    src_path = Path("/tmp/source.db")

    # Mock successful mkdir and copy
    mock_path.parent.mkdir.return_value = None
    mock_shutil.copy2.return_value = None

    # Call the method
    result = db_manager.import_database(src_path)

    # Verify behavior
    assert result is True
    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_shutil.copy2.assert_called_once_with(src_path, mock_path)


def test_import_database_failure(mocker, mock_dependencies):
    """Test import_database when the import fails."""
    from typetrace.model.database_manager import DatabaseManager

    mock_shutil, mock_path = mock_dependencies

    # Create DatabaseManager instance
    db_manager = DatabaseManager()
    src_path = Path("/tmp/source.db")

    # Mock failure with an OSError during copy
    mock_path.parent.mkdir.return_value = None
    mock_shutil.copy2.side_effect = OSError("No space left on device")

    # Call the method
    with patch("builtins.print") as mock_print:
        result = db_manager.import_database(src_path)

    # Verify behavior
    assert result is False
    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_shutil.copy2.assert_called_once_with(src_path, mock_path)
    mock_print.assert_called_once_with("Import failed: No space left on device")
