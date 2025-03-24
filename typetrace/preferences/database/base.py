"""Base handler for database preference operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final

from gi.repository import Adw


class DatabaseHandler(ABC):
    """Abstract base class for database preference handlers."""

    @abstractmethod
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """Initialize the handler.

        Args:
            parent_dialog: The parent preferences window

        """
        self.parent_dialog = parent_dialog

    @abstractmethod
    def create_row(self) -> Adw.ActionRow:
        """Create a preference row.

        Returns:
            A configured action row for the preferences dialog

        """

    @final
    def show_error_dialog(self, heading: str, message: str) -> None:
        """Show an error dialog.

        Args:
            heading: The dialog heading
            message: The error message to display

        """
        error_dialog = Adw.MessageDialog(
            transient_for=self.parent_dialog,
            heading=heading,
            body=message,
        )
        error_dialog.add_response("ok", "OK")
        error_dialog.present()

    @final
    def show_success_dialog(self, heading: str, message: str) -> None:
        """Show a success dialog.

        Args:
            heading: The dialog heading
            message: The success message to display

        """
        success_dialog = Adw.MessageDialog(
            transient_for=self.parent_dialog,
            heading=heading,
            body=message,
        )
        success_dialog.add_response("ok", "OK")
        success_dialog.present()
