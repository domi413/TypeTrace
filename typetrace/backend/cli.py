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
from gi.repository import GLib

from typetrace.config import Config, DatabasePath, ExitCodes
from typetrace.logging_setup import LoggerSetup

if TYPE_CHECKING:
    from backend.events.base import BaseEventProcessor

logger = logging.getLogger(__name__)


# --- Helper Function ---
def _run_processor_thread(processor: BaseEventProcessor) -> None:
    """Run the processor's trace method in the current thread."""
    try:
        logger.debug("Event processor thread started (PID: %d).", os.getpid())
        processor.trace()
    except Exception:
        logger.exception("Unhandled exception in event processor thread")
    finally:
        logger.debug("Event processor thread finished.")


# --- Main CLI Class ---
@final
class CLI:
    """Command-line interface for TypeTrace Backend."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_manager = DatabaseManager()
        self.__db_path = DatabasePath.DB_PATH
        self._processor_thread: threading.Thread | None = None
        self._dbus_manager: DbusServiceManager | None = None

    def _initiate_shutdown_callback(self) -> None:
        """Trigger Callback by DbusServiceManager when its loop is stopping."""
        logger.debug(
            "D-Bus service loop stopping callback triggered (backend will exit).",
        )

    def run(self) -> int:
        """Run the backend service with processor as daemon thread."""
        LoggerSetup.setup_logging()

        logger.info("TypeTrace Backend starting...")
        processor: BaseEventProcessor | None = None
        exit_code = ExitCodes.SUCCESS

        try:
            self.__db_manager.initialize_database(self.__db_path)

            def db_updated_callback() -> None:
                if self._dbus_manager:
                    GLib.idle_add(self._dbus_manager.emit_db_updated)

            # --- Start processor Thread ---
            match platform.system().lower():
                case "linux":
                    from backend.events.linux import LinuxEventProcessor

                    if not Config.IS_FLATPAK:
                        self._check_input_group()

                    processor = LinuxEventProcessor(self.__db_path, db_updated_callback)
                    processor.check_device_accessibility()

                case "darwin" | "windows":
                    from backend.events.windows_darwin import (
                        WindowsDarwinEventProcessor,
                    )

                    processor = WindowsDarwinEventProcessor(self.__db_path)

                case _:
                    logger.error("Unsupported platform: %s", platform.system())
                    return ExitCodes.PLATFORM_ERROR

            logger.debug("Starting event processor thread.")
            self._processor_thread = threading.Thread(
                target=_run_processor_thread,
                args=(processor,),
                name="EventProcessorThread",
            )
            self._processor_thread.start()

            # --- Start D-Bus Service ---
            logger.debug("Initializing D-Bus service manager...")
            self._dbus_manager = DbusServiceManager(
                stop_callback=self._initiate_shutdown_callback,
            )

            dbus_exit_code = self._dbus_manager.run()
            logger.debug("D-Bus manager finished with code: %d", dbus_exit_code)

        except PermissionError:
            logger.exception(
                "\nPlease ensure you have sufficient permissions "
                "(e.g., 'input' group).",
            )
            exit_code = ExitCodes.PERMISSION_ERROR
        except sqlite3.Error:
            logger.exception(
                "Database error: %s",
                exc_info=Config.DEBUG,
            )
            exit_code = ExitCodes.DATABASE_ERROR
        except (OSError, ValueError, RuntimeError):
            logger.exception("Unexpected error: %s")
            exit_code = ExitCodes.RUNTIME_ERROR
        finally:
            logger.debug("Initiating backend shutdown sequence (main thread exiting)..")
            if self._processor_thread and self._processor_thread.is_alive():
                logger.debug("Processor thread will be terminated.")
                processor.stop()
                self._processor_thread.join()
            logger.info("TypeTrace Backend finished.")

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
