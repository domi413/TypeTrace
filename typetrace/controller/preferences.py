"""A preferences dialog that handles various settings and preferences."""

from pathlib import Path

from gi.repository import Adw, Gio, Gtk

from typetrace.config import Config, DatabasePath
from typetrace.controller.utils import desktop_utils, dialog_utils
from typetrace.model.database_manager import DatabaseManager
from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/preferences.ui")
class Preferences(Adw.PreferencesDialog):
    """A dialog for managing application preferences."""

    __gtype_name__ = "Preferences"

    import_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    locate_button = Gtk.Template.Child()
    autostart_row = Gtk.Template.Child()

    def __init__(
        self,
        parent_window: Gtk.Window,
        db_manager: DatabaseManager,
        keystroke_store: KeystrokeStore,
    ) -> None:
        """Initialize the preferences dialog with a parent window and database manager.

        Args:
            parent_window: The main application window, used as parent for dialogs.
            db_manager: Manages database import/export operations.
            keystroke_store: Manages access to and clearing of keystroke data.

        """
        super().__init__()
        self.parent_window = parent_window

        self.db_manager = db_manager
        self.keystroke_store = keystroke_store

        self.autostart_row.set_active(desktop_utils.is_autostart_enabled())
        self.autostart_row.connect("notify::active", self._on_autostart_toggled)

        self.import_button.connect("clicked", self._on_import_clicked)
        self.export_button.connect("clicked", self._on_export_clicked)
        self.delete_button.connect("clicked", self._on_delete_clicked)
        self.locate_button.connect("clicked", self._on_locate_clicked)

    def _on_autostart_toggled(self, row: Adw.SwitchRow, *_: any) -> None:
        """Handle the autostart toggle change."""
        if row.get_active():
            success, error_msg = desktop_utils.enable_autostart()
            if success:
                dialog_utils.show_toast(self, "Backend autostart enabled")
            else:
                dialog_utils.show_error_dialog(
                    self.parent_window, "Failed to enable autostart",
                    secondary_text=error_msg,
                )
                row.set_active(False)
        else:
            success, error_msg = desktop_utils.disable_autostart()
            if success:
                dialog_utils.show_toast(self, "Backend autostart disabled")
            else:
                dialog_utils.show_error_dialog(
                    self.parent_window, "Failed to disable autostart",
                    secondary_text=error_msg,
                )
                row.set_active(True)

    def _on_export_clicked(self, _button: Gtk.Button) -> None:
        """Handle the export button click event, opens a save dialog for export."""

        def export_callback(path: Path) -> None:
            if self.db_manager.export_database(path):
                dialog_utils.show_toast(self, "Data Exported Successfully")
            else:
                dialog_utils.show_error_dialog(self.parent_window, "Export Failed")

        dialog_utils.open_file_save_dialog(
            parent=self.parent_window,
            title="Export data",
            initial_name=Config.DB_NAME,
            callback=export_callback,
        )

    def _on_import_clicked(self, _button: Gtk.Button) -> None:
        """Handle the import button click event, opens a file chooser dialog."""

        def import_callback(path: Path) -> None:
            dialog_utils.show_confirmation_dialog(
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

        dialog_utils.open_file_open_dialog(
            parent=self.parent_window,
            title="Import data",
            filters=filters,
            callback=import_callback,
        )

    def _perform_import(self, src_path: Path) -> None:
        """Perform the database import operation after user confirmation.

        Args:
            src_path: The path to the database file for import.

        """
        if self.db_manager.import_database(src_path):
            dialog_utils.show_toast(self, "Data Imported Successfully")
        else:
            dialog_utils.show_error_dialog(self.parent_window, "Import Failed")

    def _on_delete_clicked(self, _button: Gtk.Button) -> None:
        """Perform the database clear operation after user confirmation."""

        def delete_callback() -> None:
            if self.keystroke_store.clear():
                dialog_utils.show_toast(self, "Data Cleared Successfully")
            else:
                dialog_utils.show_error_dialog(self.parent_window, "Clear Failed")

        dialog_utils.show_confirmation_dialog(
            parent=self.parent_window,
            text="Confirm Database Clear",
            secondary_text="This permanently removes all recorded data, continue?",
            callback=lambda: delete_callback(),
        )

    def _on_locate_clicked(self, _button: Gtk.Button) -> None:
        """Open Filemanager where the data file is stored."""
        dialog_utils.show_folder_in_filemanager(DatabasePath.DB_PATH.parent)
