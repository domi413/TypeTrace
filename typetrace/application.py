"""Typetrace frontend application."""
from __future__ import annotations

from typing import Any, Callable

from gi.repository import Adw, Gio

from .controller.window import TypetraceWindow


class Application(Adw.Application):
    """The main application singleton class."""

    def __init__(self, application_id: str, version: str) -> None:
        """Initialize the application with default settings."""
        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.version=version
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

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
            developer_name="Unknown",
            version=self.version,
            developers=["Unknown"],
            copyright="© 2025 Unknown",
        )
        about.present(self.props.active_window)

    def on_preferences_action(self, _widget: Any, _: Any) -> None:
        """Show the application preferences dialog."""
        print("app.preferences action activated")

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
