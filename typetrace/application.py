"""Typetrace frontend application."""

from __future__ import annotations

from typing import Any, Callable
from pathlib import Path
import shutil

from gi.repository import Adw, Gio, Gtk, GLib

from .controller.window import TypetraceWindow


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
        src_path = Path(GLib.get_user_data_dir()) / "typetrace" / "TypeTrace.db"

        dialog = Gtk.FileDialog.new()
        dialog.set_title("Export data")
        dialog.set_initial_name("TypeTrace.db")

        initial_folder = Gio.File.new_for_path(
            GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
        )
        dialog.set_initial_folder(initial_folder)

        # Get the active window to use as parent for the dialog
        active_window = self.get_active_window()
        dialog.save(active_window, None, self.on_file_chooser_response, src_path)

    def on_file_chooser_response(
        self, dialog: Gtk.FileDialog, result: Gio.AsyncResult, src_path: Path
    ) -> None:
        """Handle the file chooser dialog response."""
        try:
            file = dialog.save_finish(result)
            if file:
                dst_path = Path(file.get_path())
                shutil.copy2(src_path, dst_path)

                active_window = self.get_active_window()
                success_dialog = Gtk.MessageDialog(
                    transient_for=active_window,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Data Exported Successfully",
                    secondary_text=f"Saved to: {dst_path}",
                )
                success_dialog.connect("response", lambda d, r: d.destroy())
                success_dialog.present()
        except Exception as e:
            active_window = self.get_active_window()
            error_dialog = Gtk.MessageDialog(
                transient_for=active_window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Export Failed",
                secondary_text=str(e),
            )
            error_dialog.connect("response", lambda d, r: d.destroy())
            error_dialog.present()

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
