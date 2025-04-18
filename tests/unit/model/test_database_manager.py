import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import shutil

from database_manager import DatabaseManager
from typetrace.config import DatabasePath


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    @pytest.fixture
    def database_manager(self):
        """Provide a DatabaseManager instance with mocked database path."""
        with patch.object(DatabasePath, "DB_PATH", "~/.local/share/typetrace/TypeTrace.db"):
            return DatabaseManager()

    @pytest.fixture
    def mock_shutil_copy2(self):
        """Mock shutil.copy2 to simulate file copying."""
        with patch("shutil.copy2") as mock_copy:
            yield mock_copy

    @pytest.fixture
    def mock_path_mkdir(self):
        """Mock Path.mkdir to simulate directory creation."""
        with patch.object(Path, "mkdir") as mock_mkdir:
            yield mock_mkdir

    def test_init(self):
        """Test DatabaseManager initialization."""
        with patch.object(DatabasePath, "DB_PATH", "/path/to/db"):
            db_manager = DatabaseManager()
            assert isinstance(db_manager.db_path, Path)
            assert str(db_manager.db_path) == "/path/to/db"

    def test_init_with_path_object(self):
        """Test initialization when DatabasePath.DB_PATH is a Path object."""
        with patch.object(DatabasePath, "DB_PATH", Path("/path/to/db")):
            db_manager = DatabaseManager()
            assert isinstance(db_manager.db_path, Path)
            assert str(db_manager.db_path) == "/path/to/db"

    def test_export_database_success(self, database_manager, mock_shutil_copy2):
        """Test successful database export."""
        dest_path = Path("/path/to/export.db")
        result = database_manager.export_database(dest_path)
        assert result is True
        mock_shutil_copy2.assert_called_once_with(database_manager.db_path, dest_path)

    def test_export_database_oserror(self, database_manager, mock_shutil_copy2):
        """Test export_database handling of OSError."""
        mock_shutil_copy2.side_effect = OSError("Permission denied")
        dest_path = Path("/path/to/export.db")
        result = database_manager.export_database(dest_path)
        assert result is False
        mock_shutil_copy2.assert_called_once_with(database_manager.db_path, dest_path)

    def test_export_database_nonexistent_source(self, database_manager, mock_shutil_copy2):
        """Test export_database with non-existent source file."""
        mock_shutil_copy2.side_effect = FileNotFoundError("Source file not found")
        dest_path = Path("/path/to/export.db")
        result = database_manager.export_database(dest_path)
        assert result is False
        mock_shutil_copy2.assert_called_once_with(database_manager.db_path, dest_path)

    def test_export_database_invalid_dest(self, database_manager, mock_shutil_copy2):
        """Test export_database with invalid destination (e.g., directory)."""
        mock_shutil_copy2.side_effect = IsADirectoryError("Destination is a directory")
        dest_path = Path("/path/to/directory")
        result = database_manager.export_database(dest_path)
        assert result is False
        mock_shutil_copy2.assert_called_once_with(database_manager.db_path, dest_path)

    def test_import_database_success(self, database_manager, mock_shutil_copy2, mock_path_mkdir):
        """Test successful database import."""
        src_path = Path("/path/to/source.db")
        result = database_manager.import_database(src_path)
        assert result is True
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_shutil_copy2.assert_called_once_with(src_path, database_manager.db_path)

    def test_import_database_oserror(self, database_manager, mock_shutil_copy2, mock_path_mkdir):
        """Test import_database handling of OSError."""
        mock_shutil_copy2.side_effect = OSError("Permission denied")
        src_path = Path("/path/to/source.db")
        result = database_manager.import_database(src_path)
        assert result is False
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_shutil_copy2.assert_called_once_with(src_path, database_manager.db_path)

    def test_import_database_nonexistent_source(self, database_manager, mock_shutil_copy2, mock_path_mkdir):
        """Test import_database with non-existent source file."""
        mock_shutil_copy2.side_effect = FileNotFoundError("Source file not found")
        src_path = Path("/path/to/source.db")
        result = database_manager.import_database(src_path)
        assert result is False
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_shutil_copy2.assert_called_once_with(src_path, database_manager.db_path)

    def test_import_database_mkdir_failure(self, database_manager, mock_shutil_copy2, mock_path_mkdir):
        """Test import_database handling of mkdir failure."""
        mock_path_mkdir.side_effect = OSError("Cannot create directory")
        src_path = Path("/path/to/source.db")
        result = database_manager.import_database(src_path)
        assert result is False
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_shutil_copy2.assert_not_called()

    def test_import_database_invalid_source(self, database_manager, mock_shutil_copy2, mock_path_mkdir):
        """Test import_database with invalid source (e.g., directory)."""
        mock_shutil_copy2.side_effect = IsADirectoryError("Source is a directory")
        src_path = Path("/path/to/directory")
        result = database_manager.import_database(src_path)
        assert result is False
        mock_path_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_shutil_copy2.assert_called_once_with(src_path, database_manager.db_path)