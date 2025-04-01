"""Class used to manipulate the database file."""
from __future__ import annotations

from typetrace.config import DesktopFilePath


class DesktopUtils:
    """Used for manipulations concerning the database file."""

    @staticmethod
    def is_autostart_enabled() -> bool:
        """Check if the backend autostart exists, hence enabled."""
        return DesktopFilePath.AUTOSTART_TARGET_FILE.is_symlink()

    @staticmethod
    def enable_autostart() -> tuple[bool, str | None]:
        """Create symlink to autostart desktop entry."""
        try:
            DesktopFilePath.AUTOSTART_TARGET_DIR.mkdir(parents=True, exist_ok=True)
            DesktopFilePath.AUTOSTART_TARGET_FILE.symlink_to(DesktopFilePath.AUTOSTART_SOURCE)
        except FileExistsError:
            return False, "Autostart symlink already existed."
        except PermissionError:
            return False, "Permission denied when trying to create autostart symlink."
        else:
            return True, None

    @staticmethod
    def disable_autostart() -> tuple[bool, str | None]:
        """Remove symlink to autostart desktop entry."""
        try:
            DesktopFilePath.AUTOSTART_TARGET_FILE.unlink()
        except FileNotFoundError:
            return False, "Autostart symlink already didn't exist."
        except PermissionError:
            return False, "Permission denied when trying to remove autostart symlink."
        else:
            return True, None
