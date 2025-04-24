# Incomplete Testing
"""
Test Case 1: Enable Autostart When Disabled
Test Case 2: Disable Autostart When Enabled
Test Case 3: Import Database with Valid File
Test Case 4: Import Database with Non-Existent File
Test Case 5: Export Database to Valid Location
Test Case 6: Delete Data with Confirmation
Test Case 7: Locate Database Folder
"""
import os
import gi
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Fix PyGIWarning by explicitly specifying versions
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gio, Gtk, Adw

# Load the GResource file
build_dir = os.environ.get("BUILD_DIR", "build")
resource_path = os.path.join(
    build_dir, "typetrace", "typetrace.gresource"
)  # Adjusted path
if not os.path.exists(resource_path):
    raise FileNotFoundError(f"Resource file not found: {resource_path}")
resource = Gio.Resource.load(resource_path)
resource._register()

# Import the class to be tested
from typetrace.controller.preferences import Preferences
from typetrace.model.database_manager import DatabaseManager
from typetrace.model.keystrokes import KeystrokeStore


# Fixture for the Preferences instance
@pytest.fixture
def preferences():
    parent_window = Gtk.Window()
    db_manager = MagicMock(spec=DatabaseManager)
    keystroke_store = MagicMock(spec=KeystrokeStore)
    return Preferences(parent_window, db_manager, keystroke_store)


# Test: Enable Autostart
@patch("typetrace.controller.utils.desktop_utils")
@patch("typetrace.controller.utils.dialog_utils")
def test_enable_autostart(mock_dialog_utils, mock_desktop_utils, preferences):
    mock_desktop_utils.is_autostart_enabled.return_value = False
    mock_desktop_utils.enable_autostart.return_value = (True, "")

    preferences.autostart_row.set_active(True)

    mock_desktop_utils.enable_autostart.assert_called_once()
    mock_dialog_utils.show_toast.assert_called_with(
        preferences, "Backend autostart enabled"
    )


# Test: Disable Autostart
@patch("typetrace.controller.utils.desktop_utils")
@patch("typetrace.controller.utils.dialog_utils")
def test_disable_autostart(mock_dialog_utils, mock_desktop_utils, preferences):
    mock_desktop_utils.is_autostart_enabled.return_value = True
    mock_desktop_utils.disable_autostart.return_value = (True, "")

    preferences.autostart_row.set_active(False)

    mock_desktop_utils.disable_autostart.assert_called_once()
    mock_dialog_utils.show_toast.assert_called_with(
        preferences, "Backend autostart disabled"
    )


# Test: Export Database
@patch("typetrace.controller.utils.dialog_utils")
def test_export_database(mock_dialog_utils, preferences):
    mock_dialog_utils.open_file_save_dialog.side_effect = (
        lambda *args, callback, **kwargs: callback(Path("/tmp/export.db"))
    )
    preferences.db_manager.export_database.return_value = True

    preferences._on_export_clicked(None)

    mock_dialog_utils.open_file_save_dialog.assert_called_once()
    preferences.db_manager.export_database.assert_called_with(Path("/tmp/export.db"))
    mock_dialog_utils.show_toast.assert_called_with(
        preferences, "Data Exported Successfully"
    )


# Test: Import Database with Confirmation
@patch("typetrace.controller.utils.dialog_utils")
def test_import_database(mock_dialog_utils, preferences):
    mock_dialog_utils.open_file_open_dialog.side_effect = (
        lambda *args, callback, **kwargs: callback(Path("/tmp/import.db"))
    )
    mock_dialog_utils.show_confirmation_dialog.side_effect = (
        lambda *args, callback, **kwargs: callback()
    )
    preferences.db_manager.import_database.return_value = True

    preferences._on_import_clicked(None)

    mock_dialog_utils.open_file_open_dialog.assert_called_once()
    mock_dialog_utils.show_confirmation_dialog.assert_called_once()
    preferences.db_manager.import_database.assert_called_with(Path("/tmp/import.db"))
    mock_dialog_utils.show_toast.assert_called_with(
        preferences, "Data Imported Successfully"
    )


# Test: Delete Data with Confirmation
@patch("typetrace.controller.utils.dialog_utils")
def test_delete_data(mock_dialog_utils, preferences):
    mock_dialog_utils.show_confirmation_dialog.side_effect = (
        lambda *args, callback, **kwargs: callback()
    )
    preferences.keystroke_store.clear.return_value = True

    preferences._on_delete_clicked(None)

    mock_dialog_utils.show_confirmation_dialog.assert_called_once()
    preferences.keystroke_store.clear.assert_called_once()
    mock_dialog_utils.show_toast.assert_called_with(
        preferences, "Data Cleared Successfully"
    )


# Test: Locate Database Folder
@patch("typetrace.controller.utils.dialog_utils")
def test_locate_database_folder(mock_dialog_utils, preferences):
    preferences._on_locate_clicked(None)

    mock_dialog_utils.show_folder_in_filemanager.assert_called_with(
        Path.home() / ".local" / "share" / "typetrace"
    )
