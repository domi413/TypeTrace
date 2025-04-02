import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_gi_and_utils(mocker):
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):

        class MockAdwPreferencesDialog:
            def __init__(self, *args, **kwargs):
                pass

        mock_repository.Adw = MagicMock()
        mock_repository.Adw.PreferencesDialog = MockAdwPreferencesDialog
        mock_repository.Gtk = MagicMock()
        mock_repository.Gtk.Button = MagicMock()
        mock_repository.Gtk.Template = MagicMock()
        mock_dialog_utils = {
            "show_confirmation_dialog": MagicMock(),
            "show_error_dialog": MagicMock(),
            "show_toast": MagicMock(),
            "open_file_save_dialog": MagicMock(),
        }
        with patch.dict(
            sys.modules,
            {"typetrace.controller.utils.dialog_utils": MagicMock(**mock_dialog_utils)},
        ):

            class MockTemplate:
                def __init__(self, *args, **kwargs):
                    self.resource_path = kwargs.get("resource_path")

                def __call__(self, cls):
                    return cls

                Child = MagicMock(return_value=MagicMock())

            mock_repository.Gtk.Template = MockTemplate
            yield mock_repository, mock_dialog_utils


def test_perform_import(mocker, mock_gi_and_utils):
    from typetrace.controller.preferences import Preferences

    mock_repository, mock_dialog_utils = mock_gi_and_utils
    mock_parent_window = mocker.Mock()
    mock_db_manager = mocker.Mock()
    mock_keystroke_store = mocker.Mock()
    prefs = Preferences(
        parent_window=mock_parent_window,
        db_manager=mock_db_manager,
        keystroke_store=mock_keystroke_store,
    )
    mock_path = Path("/tmp/test.db")
    mock_db_manager.import_database.return_value = True
    prefs._perform_import(mock_path)
    mock_db_manager.import_database.assert_called_once_with(mock_path)
    mock_dialog_utils["show_toast"].assert_called_once_with(
        prefs, "Data Imported Successfully"
    )
    mock_db_manager.import_database.reset_mock()
    mock_dialog_utils["show_toast"].reset_mock()
    mock_db_manager.import_database.return_value = False
    prefs._perform_import(mock_path)
    mock_db_manager.import_database.assert_called_once_with(mock_path)
    mock_dialog_utils["show_error_dialog"].assert_called_once_with(
        mock_parent_window, "Import Failed"
    )


def test_on_delete_clicked(mocker, mock_gi_and_utils):
    from typetrace.controller.preferences import Preferences

    mock_repository, mock_dialog_utils = mock_gi_and_utils
    mock_parent_window = mocker.Mock()
    mock_db_manager = mocker.Mock()
    mock_keystroke_store = mocker.Mock()
    mock_button = mocker.Mock()
    prefs = Preferences(
        parent_window=mock_parent_window,
        db_manager=mock_db_manager,
        keystroke_store=mock_keystroke_store,
    )
    prefs._on_delete_clicked(mock_button)
    mock_dialog_utils["show_confirmation_dialog"].assert_called_once_with(
        parent=mock_parent_window,
        text="Confirm Database Clear",
        secondary_text="This will remove your current data, continue?",
        callback=mocker.ANY,
    )
    delete_callback = mock_dialog_utils["show_confirmation_dialog"].call_args[1][
        "callback"
    ]
    mock_keystroke_store.clear.return_value = True
    delete_callback()
    mock_keystroke_store.clear.assert_called_once()
    mock_dialog_utils["show_toast"].assert_called_once_with(
        prefs, "Data Cleared Successfully"
    )
    mock_keystroke_store.clear.reset_mock()
    mock_dialog_utils["show_toast"].reset_mock()
    mock_keystroke_store.clear.return_value = False
    delete_callback()
    mock_keystroke_store.clear.assert_called_once()
    mock_dialog_utils["show_error_dialog"].assert_called_once_with(
        mock_parent_window, "Clear Failed"
    )


def test_on_export_clicked(mocker, mock_gi_and_utils):
    from typetrace.controller.preferences import Preferences

    mock_repository, mock_dialog_utils = mock_gi_and_utils
    mock_parent_window = mocker.Mock()
    mock_db_manager = mocker.Mock()
    mock_keystroke_store = mocker.Mock()
    mock_button = mocker.Mock()
    prefs = Preferences(
        parent_window=mock_parent_window,
        db_manager=mock_db_manager,
        keystroke_store=mock_keystroke_store,
    )
    prefs._on_export_clicked(mock_button)
    mock_dialog_utils["open_file_save_dialog"].assert_called_once_with(
        parent=mock_parent_window,
        title="Export data",
        initial_name="TypeTrace.db",  # Korrigierter Dateiname
        callback=mocker.ANY,
    )
