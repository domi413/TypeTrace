"""Command-line interface for TypeTrace."""

import argparse
import logging
import os
import platform
import sqlite3
from typing import final

from typetrace.backend.db import DatabaseManager
from typetrace.backend.logging_setup import LoggerSetup
from typetrace.config import Config, DatabasePath, ExitCodes

logger = logging.getLogger(__name__)


@final
class CLI:
    """Command-line interface for TypeTrace."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_manager = DatabaseManager()
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
            logger.info("Debug mode active: Using dummy backend.")

            # Dummy-Backend verwenden
            from typetrace.backend.ipc.linux_darwin import LinuxMacOSIPC

            backend = LinuxMacOSIPC()
            backend.register_callback(
                lambda keystroke: logger.info(f"🎯 Dummy keystroke: {keystroke}")
            )
            try:
                backend.run()
            except KeyboardInterrupt:
                backend.stop()
                logger.info("Dummy backend stopped (KeyboardInterrupt).")
            return ExitCodes.SUCCESS

        # Normaler Produktivmodus
        try:
            self.__db_manager.initialize_database(self.__db_path)

            match platform.system().lower():
                case "linux":
                    from typetrace.backend.events.linux import LinuxEventProcessor

                    if not Config.IS_FLATPAK:
                        self._check_input_group()

                    processor = LinuxEventProcessor(self.__db_path)
                    processor.check_device_accessibility()
                case "darwin" | "windows":
                    from typetrace.backend.events.windows_darwin import (
                        WindowsDarwinEventProcessor,
                    )

                    processor = WindowsDarwinEventProcessor(self.__db_path)
                case _:
                    logger.error("Unsupported platform: %s", platform.system())
                    return ExitCodes.PLATFORM_ERROR

            processor.trace()

        except PermissionError:
            logger.exception(
                "\nPlease ensure you have sufficient permissions (e.g., 'input' group)."
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

    def _check_input_group(self) -> None:
        """Check if the user is in the 'input' group on Linux."""
        import grp

        try:
            username = os.getlogin()
        except OSError:
            username = os.getenv("USER") or os.getenv("USERNAME")
            if not username:
                logger.exception("Could not determine username")
                raise PermissionError from OSError

        try:
            input_group = grp.getgrnam("input")
            if username not in input_group.gr_mem:
                logger.error("The User %s is not in the 'input' group", username)
                raise PermissionError
        except KeyError:
            logger.exception("The 'input' group does not exist")
            raise PermissionError from KeyError
