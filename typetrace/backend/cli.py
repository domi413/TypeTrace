"""Command-line interface for TypeTrace."""

import argparse
import grp
import logging
import os
import platform
import sqlite3
from pathlib import Path
from typing import final

import appdirs
from backend.config import Config, ExitCodes
from backend.db import DatabaseManager
from backend.logging_setup import LoggerSetup

logger = logging.getLogger(__name__)


@final
class CLI:
    """Command-line interface for TypeTrace."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_path = self.resolve_db_path()

    @staticmethod
    def resolve_db_path() -> Path:
        """Determine the database path using appdirs for cross-platform support."""
        data_dir = appdirs.user_data_dir(Config.APP_NAME)
        db_path = Path(data_dir) / Config.DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        return db_path

    def run(self, args: argparse.Namespace) -> int:
        """Run the main logic of the TypeTrace backend.

        Args:
            args: Command-line arguments.

        Returns:
            Exit code for the application.

        """
        if args.debug:
            Config.DEBUG = True
            LoggerSetup.setup_logging()

        try:
            match platform.system().lower():
                case "linux":
                    from backend.events.linux import LinuxEventProcessor

                    self._check_input_group()

                    processor = LinuxEventProcessor()
                    processor.check_device_accessibility()
                case "darwin" | "windows":
                    from backend.events.windows_darwin import (
                        WindowsDarwinEventProcessor,
                    )

                    processor = WindowsDarwinEventProcessor()
                case _:
                    logger.error("Unsupported platform: %s", platform.system())
                    return ExitCodes.PLATFORM_ERROR

            DatabaseManager.initialize_database(self.__db_path)
            processor.trace(self.__db_path)
        except PermissionError:
            logger.exception(
                "\nPlease ensure you have sufficient permissions "
                "(e.g., 'input' group).",
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

    @staticmethod
    def _check_input_group() -> None:
        """Check if the user is in the 'input' group on Linux."""
        username = os.getlogin()
        input_group = grp.getgrnam("input")
        if username not in input_group.gr_mem:
            logger.error("The User %s is not in the 'input' group", username)
            raise PermissionError


def main(args: argparse.Namespace) -> int:
    """Execute the TypeTrace backend.

    Args:
        args: Command-line arguments.

    Returns:
        Exit code for the application.

    """
    cli = CLI()
    return cli.run(args)
