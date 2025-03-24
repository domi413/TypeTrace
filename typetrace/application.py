"""Typetrace frontend application."""

from __future__ import annotations

from typing import Any, Callable

from gi.repository import Adw, Gio

from .controller.preferences import Preferences
from .controller.window import TypetraceWindow

DB_FILENAME = "TypeTrace.db"


class Application(Adw.Application):
    """The main application singleton class."""

    def __init__(self, application_id: str, version: str) -> None:
        """Initialize the application with default settings."""
        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.version = version
        self._setup_actions()

    def do_activate(self) -> None:
        """Activate the application.

        Raises the application's main window, creating it if necessary.
        """
        win = self.props.active_window
        if not win:
            win = TypetraceWindow(application=self)
        win.present()

    def _setup_actions(self) -> None:
        """Set up application actions and their shortcuts."""
        actions = [
            ("quit", self.quit, ["<primary>q"]),
            ("about", self.on_about_action),
            ("preferences", self.on_preferences_action),
        ]
        for args in actions:
            self.create_action(*args)

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

    def on_preferences_action(self, *_: Any) -> None:
        """Show the application preferences dialog."""
        pref_dialog = Preferences(parent_window=self.props.active_window)
        pref_dialog.present(self.props.active_window)

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
