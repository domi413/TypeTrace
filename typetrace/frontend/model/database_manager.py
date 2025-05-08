"""Class used to manipulate the database file."""

import logging
import shutil
from pathlib import Path
from typing import ClassVar

from config import DatabasePath
from gi.repository import GObject

logger = logging.getLogger(__name__)


class DatabaseManager(GObject.Object):
    """Used for manipulations concerning the database file."""

    def __init__(self) -> None:
        """Construct an instance of DatabaseManager."""
        super().__init__()
        self.db_path = Path(DatabasePath.DB_PATH)

    __gsignals__: ClassVar[dict] = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def export_database(self, dest_path: Path) -> bool:
        """Export the database to the specified destination path."""
        try:
            shutil.copy2(self.db_path, dest_path)
        except OSError:
            logger.exception("Failed to export database to %s", dest_path)
            return False
        else:
            logger.debug("Exported database from %s to %s", self.db_path, dest_path)
            return True

    def import_database(self, src_path: Path) -> bool:
        """Import database from the source path, overwriting the current one."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, self.db_path)
        except OSError:
            logger.exception("Failed to import database from %s", src_path)
            return False
        else:
            logger.debug("Imported database from %s to %s", src_path, self.db_path)
            self.emit("changed")
            return True
