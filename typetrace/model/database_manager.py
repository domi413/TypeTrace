"""Class used to manipulate the database file."""

import shutil
from pathlib import Path

from typetrace.config import Config


class DatabaseManager:
    """Used for manipulations concerning the database file."""

    def __init__(self) -> None:
        """Construct an instance of DatabaseManager."""
        self.db_path = Path(Config.DB_PATH)

    def export_database(self, dest_path: Path) -> bool:
        """Export the database to the specified destination path."""
        try:
            shutil.copy2(self.db_path, dest_path)
        except OSError:
            return False
        else:
            return True

    def import_database(self, src_path: Path) -> bool:
        """Import database from the source path, overwriting the current one."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, self.db_path)
        except OSError:
            return False
        else:
            return True
