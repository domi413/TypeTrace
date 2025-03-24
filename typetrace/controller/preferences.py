"""A preferences dialog that handles various settings and preferences."""

from pathlib import Path

from gi.repository import Adw, Gio, Gtk

from typetrace.controller.utils.dialog_utils import (
    show_confirmation_dialog,
    show_error_dialog,
    show_open_dialog,
    show_save_dialog,
    show_toast,
)
from typetrace.model.database_manager import DatabaseManager


@Gtk.Template(resource_path="/edu/ost/typetrace/view/preferences.ui")
class Preferences(Adw.PreferencesDialog):
    """A dialog for managing application preferences."""

    __gtype_name__ = "Preferences"

    import_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()

    def __init__(self, parent_window: Gtk.Window, db_manager: DatabaseManager) -> None:
        """Initialize the preferences dialog with a parent window and database manager.

        Args:
            parent_window (Gtk.Window): The parent window for the dialog.
            db_manager (DatabaseManager): The database manager instance.

        """
        super().__init__()
        self.parent_window = parent_window
        self.db_manager = db_manager

        self.import_button.connect("clicked", self.on_import_clicked)
        self.export_button.connect("clicked", self.on_export_clicked)

    def on_export_clicked(self, _button: Gtk.Button) -> None:
        """Handle the export button click event by opening a save dialog."""
        def export_callback(path: Path) -> None:
            if self.db_manager.export_database(path):
                show_toast(self, "Data Exported Successfully")
            else:
                show_error_dialog(self.parent_window, "Export Failed")

        show_save_dialog(
            parent=self.parent_window,
            title="Export data",
            initial_name="typetrace.db",
            callback=export_callback,
        )

    def on_import_clicked(self, _button: Gtk.Button) -> None:
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

        show_open_dialog(
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
