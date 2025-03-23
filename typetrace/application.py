"""Typetrace frontend application."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable

from gi.repository import Adw, Gio, GLib, Gtk

from .controller.window import TypetraceWindow

DB_FILENAME = "TypeTrace.db"


class Application(Adw.Application):
    """The main application singleton class."""

    def __init__(self, application_id: str, version: str) -> None:
        """Initialize the application with default settings."""
        super().__init__(application_id=application_id, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.version = version
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)
        self.create_action("export", self.on_export_activate)
        self.create_action("import", self.on_import_activate)

    def do_activate(self) -> None:
        """Activate the application.

        Raises the application's main window, creating it if necessary.
        """
        win = self.props.active_window
        if not win:
            win = TypetraceWindow(application=self)
        win.present()

    def on_about_action(self, *_: Any) -> None:
        """Display the about dialog with application information."""
        about = Adw.AboutDialog(
            application_name="TypeTrace",
            application_icon="edu.ost.typetrace",
            website="https://github.com/domi413/TypeTrace",
            version=self.version,
            developers=[
                "David Yves Bachmann",
                "Dominik Bühler",
                "Gioele Petrillo",
                "Ivan Knöfler",
                "Mustafa Alali",
            ],
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, _widget: Any, _: Any) -> None:
        """Show the application preferences dialog."""
        print("app.preferences action activated")

    def on_export_activate(self, _action: Gio.SimpleAction, _parameter: None) -> None:
        """Handle export action activation."""
        src_path = Path(GLib.get_user_data_dir()) / "typetrace" / DB_FILENAME

        dialog = self._create_file_dialog(
            title="Export data",
            initial_name=DB_FILENAME,
            is_save=True,
        )

        active_window = self.get_active_window()
        dialog.save(active_window, None, self._handle_export_response, src_path)

    def _handle_export_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
        src_path: Path,
    ) -> None:
        """Handle the export file dialog response."""
        try:
            file = dialog.save_finish(result)
            if file:
                dst_path = Path(file.get_path())
                shutil.copy2(src_path, dst_path)
                self._show_message_dialog(
                    message_type=Gtk.MessageType.INFO,
                    text="Data Exported Successfully",
                    secondary_text=f"Saved to: {dst_path}",
                )
        except GLib.Error as e:
            # If dialog is closed (escape or cancel button) don't show error
            if e.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                return
            self._show_message_dialog(
                message_type=Gtk.MessageType.ERROR,
                text="Export Failed",
                secondary_text=str(e),
            )
        except OSError as e:
            self._show_message_dialog(
                message_type=Gtk.MessageType.ERROR,
                text="Export Failed",
                secondary_text=str(e),
            )

    def on_import_activate(self, _action: Gio.SimpleAction, _parameter: None) -> None:
        """Handle import action activation."""
        dst_path = Path(GLib.get_user_data_dir()) / "typetrace" / DB_FILENAME

        dialog = self._create_file_dialog(
            title="Import data",
            is_save=False,
        )

        file_filter = Gtk.FileFilter()
        file_filter.set_name("Database files")
        file_filter.add_pattern("*.db")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        dialog.set_filters(filters)

        active_window = self.get_active_window()
        dialog.open(active_window, None, self._handle_import_response, dst_path)

    def _handle_import_response(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
        dst_path: Path,
    ) -> None:
        """Handle the import file dialog response."""
        try:
            file = dialog.open_finish(result)
            if file:
                src_path = Path(file.get_path())
                self._show_confirmation_dialog(
                    text="Confirm Data Import",
                    secondary_text="This will override your current data. Do you want to continue?",
                    callback=lambda: self._perform_import(src_path, dst_path),
                )
        except GLib.Error as e:
            # If dialog is closed (escape or cancel button) don't show error
            if e.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                return
            self._show_message_dialog(
                message_type=Gtk.MessageType.ERROR,
                text="Import Failed",
                secondary_text=str(e),
            )
        except OSError as e:
            self._show_message_dialog(
                message_type=Gtk.MessageType.ERROR,
                text="Import Failed",
                secondary_text=str(e),
            )

    def _perform_import(self, src_path: Path, dst_path: Path) -> None:
        """Perform the actual import operation."""
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            self._show_message_dialog(
                message_type=Gtk.MessageType.INFO,
                text="Data Imported Successfully",
                secondary_text="Data has been imported. Refresh the application to see changes.",
            )
        except OSError as e:
            self._show_message_dialog(
                message_type=Gtk.MessageType.ERROR,
                text="Import Failed",
                secondary_text=str(e),
            )

    def _create_file_dialog(
        self,
        title: str,
        initial_name: str | None = None,
        *,
        is_save: bool = True,
    ) -> Gtk.FileDialog:
        """Create and configure a file dialog.

        Args:
            title: The title of the dialog
            initial_name: Optional initial filename (for save dialogs)
            is_save: Whether this is a save dialog (True) or open dialog (False)

        """
        dialog = Gtk.FileDialog.new()
        dialog.set_title(title)

        if initial_name and is_save:
            dialog.set_initial_name(initial_name)

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
        """Show a message dialog with the given parameters.

        Args:
            message_type: The type of message (INFO, WARNING, ERROR, etc.)
            text: The primary text to display
            secondary_text: Optional secondary text to display

        """
        active_window = self.get_active_window()
        dialog = Gtk.MessageDialog(
            transient_for=active_window,
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
        """Show a confirmation dialog with OK/Cancel buttons.

        Args:
            text: The primary text to display
            secondary_text: The secondary text to display
            callback: Function to call if the user confirms

        """
        active_window = self.get_active_window()
        dialog = Gtk.MessageDialog(
            transient_for=active_window,
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

    def create_action(
        self,
        name: str,
        callback: Callable[..., Any],
        shortcuts: list[str] | None = None,
    ) -> None:
        """Add an application action with optional keyboard shortcuts.

        Args:
            name: The name of the action to create
            callback: The function to call when the action is activated
            shortcuts: List of keyboard accelerators for the action

        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
