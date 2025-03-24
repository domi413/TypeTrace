"""Database preferences TypeTrace application."""

from __future__ import annotations

from typing import final, override

from gi.repository import Adw

from typetrace.preferences.base import BasePreferencesGroup
from typetrace.preferences.database.delete_handler import DatabaseDeleteHandler
from typetrace.preferences.database.export_handler import DatabaseExportHandler
from typetrace.preferences.database.import_handler import DatabaseImportHandler
from typetrace.preferences.database.open_handler import DatabaseOpenHandler


@final
class DatabasePreferencesGroup(BasePreferencesGroup):
    """Group for database-related preferences."""

    @override
    def __init__(self, parent_dialog: Adw.PreferencesWindow) -> None:
        """See base class."""
        super().__init__(parent_dialog, title="Database")
        self._import_handler = DatabaseImportHandler(parent_dialog)
        self._export_handler = DatabaseExportHandler(parent_dialog)
        self._open_handler = DatabaseOpenHandler(parent_dialog)
        self._delete_handler = DatabaseDeleteHandler(parent_dialog)
        self._initialize()

    @override
    def _initialize(self) -> None:
        """See base class."""
        self.add(self._import_handler.create_row())
        self.add(self._export_handler.create_row())
        self.add(self._open_handler.create_row())
        self.add(self._delete_handler.create_row())
