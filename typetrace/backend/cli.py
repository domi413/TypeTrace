"""Command-line interface for TypeTrace."""

import argparse
import grp
import logging
import os
import sqlite3
from pathlib import Path

import appdirs

from .config import Config, ExitCodes

logger = logging.getLogger(__name__)


class CLI:
    """Command-line interface for TypeTrace."""

    def __init__(self):
        """Initialize the CLI."""
        self.db_path = self.resolve_db_path()

    @staticmethod
    def resolve_db_path() -> Path:
        """Determine the database path using appdirs for cross-platform support."""
        app_name = Config.PROJECT_NAME.lower()
        data_dir = appdirs.user_data_dir(app_name)
        db_path = Path(data_dir) / Config.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        return db_path

    @staticmethod
    def check_input_group() -> None:
        """Check if the current user is in the 'input' group."""
        username = os.getlogin()
        input_group = grp.getgrnam("input")
        if username not in input_group.gr_mem:
            logger.error("The User %s is not in the 'input' group", username)
            raise PermissionError

    def run(self, args: argparse.Namespace) -> int:
        """Run the main logic of the TypeTrace backend.

        Returns:
            Exit code for the application.

        """
        if args.debug:
            # Update the global DEBUG variable
            from .config import Config

            Config.DEBUG = True
            from .logging_setup import LoggerSetup

            LoggerSetup.setup_logging()

        try:
            self.check_input_group()

            from .devices.linux import check_device_accessibility

            check_device_accessibility()
            db_path: Path = self.db_path

            from .db import DatabaseManager

            DatabaseManager.initialize_database(db_path)

            from .events import trace_keys

            trace_keys(db_path)
        except PermissionError:
            logger.exception(
                "\nPlease ensure you have sufficient permissions (e.g., 'input' group).",
            )
            return ExitCodes.PERMISSION_ERROR
        except sqlite3.Error:
            logger.exception("Database error")
            return ExitCodes.DATABASE_ERROR
        except (OSError, ValueError, RuntimeError):
            logger.exception("Unexpected error")
            return ExitCodes.RUNTIME_ERROR
        else:
            return ExitCodes.SUCCESS
