"""Unit tests for the DatabaseFileHandler class.

These tests cover the export and import functionality of the database file,
including edge cases and the emission of the 'changed' signal on import.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from typetrace.frontend.model.db_filehandler import DatabaseFileHandler


@pytest.fixture()
def db_file_handler() -> DatabaseFileHandler:
    """Fixture to create a DatabaseFileHandler instance."""
    return DatabaseFileHandler()


def test_export_database_success(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test exporting the database to a specified destination."""
    dest_path = tmp_path / "test_export.db"
    db_file_handler.db_path = tmp_path / "test.db"
    db_file_handler.db_path.touch()

    assert db_file_handler.export_database(dest_path)
    assert dest_path.exists()


def test_export_database_failure(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test the failure of the export when the source file doesn't exist."""
    dest_path = tmp_path / "test_export.db"
    db_file_handler.db_path = tmp_path / "non_existent_file.db"

    assert not db_file_handler.export_database(dest_path)
    assert not dest_path.exists()


def test_import_database_success(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test importing a database from the source path."""
    source_path = tmp_path / "test_import.db"
    source_path.touch()  # Mock an existing source file

    db_file_handler.db_path = tmp_path / "test.db"

    assert db_file_handler.import_database(source_path)
    assert db_file_handler.db_path.exists()


def test_import_database_failure(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test importing a database with a non-existent source file."""
    source_path = tmp_path / "non_existent_file.db"
    db_file_handler.db_path = tmp_path / "test.db"

    assert not db_file_handler.import_database(source_path)
    assert not db_file_handler.db_path.exists()


def test_emit_changed_signal_on_import(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test that the 'changed' signal is emitted on database import."""
    source_path = tmp_path / "test_import.db"
    source_path.touch()
    db_file_handler.db_path = tmp_path / "test.db"

    with patch.object(db_file_handler, "emit") as mock_emit:
        db_file_handler.import_database(source_path)
        mock_emit.assert_called_once_with("changed")


def test_export_database_edge_case(
    db_file_handler: DatabaseFileHandler, tmp_path: Path,
) -> None:
    """Test edge case where database file is empty."""
    dest_path = tmp_path / "test_export.db"
    db_file_handler.db_path = tmp_path / "empty.db"
    db_file_handler.db_path.touch()

    assert db_file_handler.export_database(dest_path)
    assert dest_path.exists()
