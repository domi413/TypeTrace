"""Command-line interface for TypeTrace."""

import argparse
import logging
import os
import platform
import sqlite3
from typing import final

from backend.db import DatabaseManager
from backend.logging_setup import LoggerSetup

from typetrace.config import Config, DatabasePath, ExitCodes

logger = logging.getLogger(__name__)


@final
class CLI:
    """Command-line interface for TypeTrace."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_path = DatabasePath.DB_PATH

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
        import grp

        try:
            username = os.getlogin()
        except OSError:
            username = os.getenv("USER") or os.getenv("USERNAME")
        input_group = grp.getgrnam("input")
        if username not in input_group.gr_mem:
            logger.error("The User %s is not in the 'input' group", username)
            raise PermissionError
