"""Base classes and utilities for preferences module."""

from __future__ import annotations

from abc import abstractmethod

from gi.repository import Adw


class BasePreferencesGroup(Adw.PreferencesGroup):
    """Base class for preference groups in TypeTrace."""

    @abstractmethod
    def __init__(self, parent_dialog: Adw.PreferencesWindow, title: str) -> None:
        """Initialize the preferences group.

        Args:
            parent_dialog: The parent preferences dialog
            title: The title for this preferences group

        """
        super().__init__(title=title)
        self.parent_dialog = parent_dialog

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize all preference rows for this group."""
