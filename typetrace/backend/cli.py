"""Command-line interface for TypeTrace."""

from __future__ import annotations

import logging
import os
import platform
import sqlite3
import threading
from typing import TYPE_CHECKING, final

from backend.db import DatabaseManager
from backend.dbus_service import DbusServiceManager
from backend.logging_setup import LoggerSetup

from typetrace.config import Config, DatabasePath, ExitCodes

if TYPE_CHECKING:
    import argparse

    from backend.events.base import BaseEventProcessor

logger = logging.getLogger(__name__)


# --- Helper Function ---
def _run_processor_thread(processor: BaseEventProcessor) -> None:
    """Run the processor's trace method in the current thread."""
    try:
        # NOTE: Processor runs as daemon, may be terminated abruptly.
        logger.info("Event processor daemon thread started (PID: %d).", os.getpid())
        processor.trace()
    except Exception:
        logger.exception("Unhandled exception in event processor daemon thread")
    finally:
        # This block might not run fully if thread is terminated abruptly.
        logger.info("Event processor daemon thread finished (possibly abruptly).")


# --- Main CLI Class ---
@final
class CLI:
    """Command-line interface for TypeTrace Backend."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_manager = DatabaseManager()
        self.__db_path = DatabasePath.DB_PATH
        # Thread reference might still be useful for is_alive checks if needed elsewhere
        self._processor_thread: threading.Thread | None = None
        self._dbus_manager: DbusServiceManager | None = None

    def _get_processor_class(self) -> type[BaseEventProcessor] | None:
        """Determine the correct event processor class based on the platform."""
        system = platform.system().lower()
        logger.info("Detected platform: %s", system)
        if system == "linux":
            from backend.events.linux import LinuxEventProcessor

            return LinuxEventProcessor
        if system in ("darwin", "windows"):
            from backend.events.windows_darwin import (
                WindowsDarwinEventProcessor,
            )

            return WindowsDarwinEventProcessor
        logger.error("Unsupported platform: %s", platform.system())
        return None

    def _initiate_shutdown_callback(self) -> None:
        """Trigger Callback by DbusServiceManager when its loop is stopping."""
        # This callback signals the D-Bus loop should stop.
        # The daemon processor thread will exit when the main thread finishes.
        logger.info(
            "D-Bus service loop stopping callback triggered (backend will exit).",
        )

    def run(self, args: argparse.Namespace) -> int:  # noqa: C901
        """Run the backend service with processor as daemon thread."""
        if args.debug:
            Config.DEBUG = True
        LoggerSetup.setup_logging()

        logger.info("TypeTrace Backend starting...")
        exit_code = ExitCodes.SUCCESS
        processor: BaseEventProcessor | None = None

        try:
            self.__db_manager.initialize_database(self.__db_path)

            processor_class = self._get_processor_class()
            if not processor_class:
                return ExitCodes.PLATFORM_ERROR

            processor = processor_class(self.__db_path)
            if hasattr(processor, "check_device_accessibility"):
                processor.check_device_accessibility()

            # --- Start Processor Thread as DAEMON ---
            # NOTE: Using daemon thread because processor's internal signal
            # handling cannot be set up from a secondary thread, and modifying
            # the processor is disallowed. This means abrupt termination.
            logger.info("Starting event processor thread as DAEMON.")
            self._processor_thread = threading.Thread(
                target=_run_processor_thread,
                args=(processor,),
                name="EventProcessorThread",
            )
            # *** Set daemon=True ***
            self._processor_thread.daemon = True
            self._processor_thread.start()

            # --- Start D-Bus Service ---
            logger.info("Initializing D-Bus service manager...")
            self._dbus_manager = DbusServiceManager(
                stop_callback=self._initiate_shutdown_callback,
            )

            # Blocks main thread until D-Bus loop stops
            dbus_exit_code = self._dbus_manager.run()
            logger.info("D-Bus manager run() finished with code: %d", dbus_exit_code)
            if dbus_exit_code != 0:
                exit_code = ExitCodes.RUNTIME_ERROR

            match platform.system().lower():
                case "linux":
                    from backend.events.linux import LinuxEventProcessor

                    if not Config.IS_FLATPAK:
                        self._check_input_group()

                    processor = LinuxEventProcessor(self.__db_path)
                    processor.check_device_accessibility()

                case "darwin" | "windows":
                    from backend.events.windows_darwin import (
                        WindowsDarwinEventProcessor,
                    )

                    processor = WindowsDarwinEventProcessor(self.__db_path)

                case _:
                    logger.error("Unsupported platform: %s", platform.system())
                    return ExitCodes.PLATFORM_ERROR

        # --- Handle Setup Errors ---
        except PermissionError:
            logger.exception(
                "Permission error during setup: %s", exc_info=Config.DEBUG,
            )
            exit_code = ExitCodes.PERMISSION_ERROR
        except sqlite3.Error:
            logger.exception(
                "Database error during setup: %s", exc_info=Config.DEBUG,
            )
            exit_code = ExitCodes.DATABASE_ERROR
        finally:
            # No need to signal or join the daemon thread.
            logger.info("Initiating backend shutdown sequence (main thread exiting)...")
            if self._processor_thread and self._processor_thread.is_alive():
                logger.info("Processor daemon thread will be terminated.")

            logger.info("TypeTrace Backend finished.")
            # Main thread exits here, interpreter terminates daemon threads.

        return exit_code

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
