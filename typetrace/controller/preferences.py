"""A preferences dialog that handles various settings and preferences."""

from pathlib import Path

from gi.repository import Adw, Gio, Gtk

from typetrace.config import DatabasePath
from typetrace.controller.utils.dialog_utils import (
    open_file_open_dialog,
    open_file_save_dialog,
    show_confirmation_dialog,
    show_error_dialog,
    show_toast,
)
from typetrace.model.database_manager import DatabaseManager
from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/preferences.ui")
class Preferences(Adw.PreferencesDialog):
    """A dialog for managing application preferences."""

    __gtype_name__ = "Preferences"

    import_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(
        self,
        parent_window: Gtk.Window,
        db_manager: DatabaseManager,
        keystroke_store: KeystrokeStore,
    ) -> None:
        """Initialize the preferences dialog with a parent window and database manager.

        Args:
            parent_window (Gtk.Window): The parent window for the dialog.
            db_manager (DatabaseManager): The database manager instance.
            keystroke_store: (KeystrokeStore): Access to keystrokes database.

        """
        super().__init__()
        self.parent_window = parent_window

        self.db_manager = db_manager
        self.keystroke_store = keystroke_store

        self.import_button.connect("clicked", self._on_import_clicked)
        self.export_button.connect("clicked", self._on_export_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)

    def _on_export_clicked(self, _button: Gtk.Button) -> None:
        """Handle the export button click event by opening a save dialog."""

        def export_callback(path: Path) -> None:
            if self.db_manager.export_database(path):
                show_toast(self, "Data Exported Successfully")
            else:
                show_error_dialog(self.parent_window, "Export Failed")

        open_file_save_dialog(
            parent=self.parent_window,
            title="Export data",
            initial_name=str(DatabasePath.DB_PATH),
            callback=export_callback,
        )

    def _on_import_clicked(self, _button: Gtk.Button) -> None:
        """Handle the import button click event by opening a file chooser dialog."""

        def import_callback(path: Path) -> None:
            show_confirmation_dialog(
                parent=self.parent_window,
                text="Confirm Data Import",
                secondary_text="This will override your current data, continue?",
                callback=lambda: self._perform_import(path),
            )

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Database files")
        file_filter.add_pattern("*.db")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)

        open_file_open_dialog(
            parent=self.parent_window,
            title="Import data",
            filters=filters,
            callback=import_callback,
        )

    def _perform_import(self, src_path: Path) -> None:
        """Perform the database import operation after user confirmation.

        Args:
            src_path (Path): The path to the database file to import.

        """
        if self.db_manager.import_database(src_path):
            show_toast(self, "Data Imported Successfully")
        else:
            show_error_dialog(self.parent_window, "Import Failed")

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        """Perform the database clear operation after user confirmation."""

        def delete_callback() -> None:
            if self.keystroke_store.clear():
                show_toast(self, "Data Cleared Successfully")
            else:
                show_error_dialog(self.parent_window, "Clear Failed")

        show_confirmation_dialog(
            parent=self.parent_window,
            text="Confirm Database Clear",
            secondary_text="This will remove your current data, continue?",
            callback=lambda: delete_callback(),
        )
