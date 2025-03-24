"""A preferences dialog that handles various settings and preferences."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from backend.cli import DB_NAME, resolve_db_path
from gi.repository import Adw, Gio, GLib, Gtk


@Gtk.Template(resource_path="/edu/ost/typetrace/view/preferences.ui")
class Preferences(Adw.PreferencesDialog):
    """A preferences dialog that handles various settings and preferences."""

    __gtype_name__ = "Preferences"

    import_button = Gtk.Template.Child()
    export_button = Gtk.Template.Child()

    def __init__(self, parent_window: Gtk.Window, **kwargs) -> None:
        """Initialize the preferences window and connect button signals."""
        super().__init__(**kwargs)
        self.parent_window = parent_window
        self.db_path = resolve_db_path()

        self.import_button.connect("clicked", self.on_import_clicked)
        self.export_button.connect("clicked", self.on_export_clicked)

    def on_export_clicked(self, _button: Gtk.Button) -> None:
        """Handle export button click."""
        dialog = self._create_file_dialog(
            title="Export data",
            initial_name=DB_NAME,
            is_save=True,
        )
        dialog.save(self.parent_window, None, self._handle_export_response)

    def on_import_clicked(self, _button: Gtk.Button) -> None:
        """Handle import button click."""
        dialog = self._create_file_dialog(
            title="Import data",
            is_save=False,
        )

        # Set up file filter for database files
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Database files")
        file_filter.add_pattern("*.db")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        dialog.set_filters(filters)

        dialog.open(self.parent_window, None, self._handle_import_response)

    def _handle_export_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        """Handle the export file dialog response."""
        try:
            file = dialog.save_finish(result)
            if file:
                dst_path = Path(file.get_path())
                shutil.copy2(self.db_path, dst_path)
                self._show_toast("Data Exported Successfully")
        except GLib.Error as e:
            if e.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                return
            self._show_error_dialog("Export Failed", str(e))
        except OSError as e:
            self._show_error_dialog("Export Failed", str(e))

    def _handle_import_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        """Handle the import file dialog response."""
        try:
            file = dialog.open_finish(result)
            if file:
                src_path = Path(file.get_path())
                self._show_confirmation_dialog(
                    text="Confirm Data Import",
                    secondary_text="This will override your current data, continue?",
                    callback=lambda: self._perform_import(src_path),
                )
        except GLib.Error as e:
            if e.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                return
            self._show_error_dialog("Import Failed", str(e))
        except OSError as e:
            self._show_error_dialog("Import Failed", str(e))

    def _perform_import(self, src_path: Path) -> None:
        """Perform the actual import operation."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, self.db_path)
            self._show_toast("Data Imported Successfully")
        except OSError as e:
            self._show_error_dialog("Import Failed", str(e))

    def _show_toast(self, message: str, timeout: int = 3) -> None:
        """Show a toast notification."""
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        self.add_toast(toast)

    def _show_error_dialog(self, text: str, secondary_text: str | None = None) -> None:
        """Show an error dialog with the given message."""
        self._show_message_dialog(
            message_type=Gtk.MessageType.ERROR,
            text=text,
            secondary_text=secondary_text,
        )

    def _create_file_dialog(
        self,
        title: str,
        initial_name: str | None = None,
        *,
        is_save: bool = True,
    ) -> Gtk.FileDialog:
        """Create and configure a file dialog."""
        dialog = Gtk.FileDialog.new()
        dialog.set_title(title)

        if initial_name and is_save:
            dialog.set_initial_name(initial_name)

        # Set initial folder to user's download directory
        initial_folder = Gio.File.new_for_path(
            GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD),
        )
        dialog.set_initial_folder(initial_folder)

        return dialog

    def _show_message_dialog(
        self,
        message_type: Gtk.MessageType,
        text: str,
        secondary_text: str | None = None,
    ) -> None:
        """Show a message dialog with the given parameters."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=text,
            secondary_text=secondary_text,
        )
        dialog.connect("response", lambda d, _: d.destroy())
        dialog.present()

    def _show_confirmation_dialog(
        self,
        text: str,
        secondary_text: str,
        callback: Callable[[], None],
    ) -> None:
        """Show a confirmation dialog with OK/Cancel buttons."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=text,
            secondary_text=secondary_text,
        )

        def on_response(dialog: Gtk.MessageDialog, response_id: int) -> None:
            dialog.destroy()
            if response_id == Gtk.ResponseType.OK:
                callback()

        dialog.connect("response", on_response)
        dialog.present()
