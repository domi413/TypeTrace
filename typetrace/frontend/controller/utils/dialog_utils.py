"""Utilities for creating and managing common GTK/Adwaita dialogs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import dbus
from gi.repository import Adw, Gio, GLib, Gtk

from typetrace.config import Config

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def show_toast(window: Gtk.Window, message: str, timeout: int = 3) -> None:
    """Display an Adwaita toast notification anchored to a window.

    Args:
        window: The parent Gtk.Window to attach the toast to.
        message: The text message to display in the toast.
        timeout: Duration in seconds the toast remains visible (0 for indefinite).

    """
    toast = Adw.Toast.new(message)
    toast.set_timeout(timeout)
    window.add_toast(toast)


def show_error_dialog(
    window: Gtk.Window,
    text: str,
    secondary_text: str | None = None,
) -> None:
    """Display a modal error dialog using Adw.AlertDialog.

    Args:
        window: The parent Gtk.Window for the dialog.
        text: The primary heading text for the error message.
        secondary_text: Optional detailed body text for the error.

    """
    dialog = Adw.AlertDialog(
        heading=text,
        body=secondary_text or "",
    )
    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")
    dialog.present(window)


def open_file_save_dialog(
    parent: Gtk.Window,
    title: str,
    initial_name: str,
    callback: Callable[[Path], None],
    initial_folder: str | Path | None = None,
) -> None:
    """Open a 'Save As...' file chooser dialog using Gtk.FileDialog.

    Args:
        parent: The parent Gtk.Window for the dialog.
        title: The title displayed in the dialog window.
        initial_name: The suggested filename to save as.
        callback: A function to call with the chosen Path object.
        initial_folder: Optional path to open the dialog at.

    """
    dialog = Gtk.FileDialog()
    dialog.set_title(title)
    dialog.set_initial_name(initial_name)

    if initial_folder:
        folder = Gio.File.new_for_path(str(initial_folder))
        dialog.set_initial_folder(folder)

    def on_response(dialog: Gtk.FileDialog, res: Gio.Task, _: Gtk.Window) -> None:
        try:
            file = dialog.save_finish(res)
            if file:
                callback(Path(file.get_path()))
        except GLib.Error:
            logger.exception("Failed to save file in dialog: %s", title)

    dialog.save(parent, None, on_response, parent)


def open_file_open_dialog(
    parent: Gtk.Window,
    title: str,
    filters: Gio.ListStore[Gtk.FileFilter],
    callback: Callable[[Path], None],
    initial_folder: str | Path | None = None,
) -> None:
    """Open a file chooser dialog using Gtk.FileDialog.

    Args:
        parent: The parent Gtk.Window for the dialog.
        title: The title displayed in the dialog window.
        filters: A Gio.ListStore containing Gtk.FileFilter objects to apply.
        callback: A function to call with the chosen Path object if selected.
        initial_folder: Optional path to open the dialog at.

    """
    dialog = Gtk.FileDialog()
    dialog.set_title(title)

    if filters:
        dialog.set_filters(filters)

    if initial_folder:
        folder = Gio.File.new_for_path(str(initial_folder))
        dialog.set_initial_folder(folder)

    def on_response(dialog: Gtk.FileDialog, res: Gio.Task, _: Gtk.Window) -> None:
        try:
            file = dialog.open_finish(res)
            if file:
                callback(Path(file.get_path()))
        except GLib.Error:
            logger.exception("Failed to open file in dialog: %s", title)

    dialog.open(parent, None, on_response, parent)


def show_confirmation_dialog(
    parent: Gtk.Window,
    text: str,
    secondary_text: str,
    callback: Callable[[], None],
) -> None:
    """Show a modal confirmation dialog using Adw.AlertDialog with 'Yes'/'No'.

    The 'Yes' button has a destructive appearance.

    Args:
        parent: The parent Gtk.Window for the dialog.
        text: The primary heading text for the confirmation question.
        secondary_text: Additional body text explaining the action.
        callback: A function to call if the user clicks 'Yes'.

    """
    dialog = Adw.AlertDialog(
        heading=text,
        body=secondary_text,
    )
    dialog.add_response("no", "No")
    dialog.add_response("yes", "Yes")
    dialog.set_response_appearance("yes", Adw.ResponseAppearance.DESTRUCTIVE)
    dialog.set_default_response("no")
    dialog.set_close_response("no")

    def on_response(_dialog: Adw.AlertDialog, response_id: str) -> None:
        """Handle dialog response."""
        if response_id == "yes":
            callback()

    dialog.connect("response", on_response)
    dialog.present(parent)


def show_folder_in_filemanager(
    folder_path: str | Path,
) -> None:
    """Open the system's default file manager at the specified folder path.

    Args:
        folder_path: The path to the folder to open in the file manager.

    """
    try:
        path = Path(folder_path).resolve()

        if Config.IS_FLATPAK:
            try:
                bus = dbus.SessionBus()
                obj = bus.get_object(
                    "org.freedesktop.FileManager1",
                    "/org/freedesktop/FileManager1",
                )
                interface = dbus.Interface(obj, "org.freedesktop.FileManager1")
                uri = f"file://{path}"
                interface.ShowFolders([uri], "")
            except dbus.DBusException:
                logger.exception(
                    "Failed to open folder in file manager via D-Bus: %s",
                    path,
                )
        else:
            # Non-Flatpak: Use GIO
            gfile = Gio.File.new_for_path(str(path))
            try:
                app_info = Gio.AppInfo.get_default_for_type(
                    "inode/directory",
                    must_support_uris=True,
                )
                if app_info:
                    app_info.launch([gfile], None)
            except GLib.Error:
                logger.exception(
                    "Failed to open folder in file manager via GIO: %s",
                    path,
                )
    except ValueError:
        logger.exception("Invalid folder path: %s", folder_path)
