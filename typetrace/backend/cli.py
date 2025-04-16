"""Command-line interface for TypeTrace."""

from __future__ import annotations

import logging
import os
import platform
import signal
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


# Helper Function
def _run_processor_thread(processor: BaseEventProcessor) -> None:
    """Run the processor's trace method in the current thread."""
    try:
        logger.info("Event processor thread started (PID: %d).", os.getpid())
        # This call blocks until the processor stops
        processor.trace()
    except Exception:
        # Log exceptions occurring within the thread
        logger.exception("Unhandled exception in event processor thread")
    finally:
        # This might execute if trace() returns normally or via exception,
        # but potentially not on abrupt signal termination depending on internals.
        logger.info("Event processor thread finished.")


@final
class CLI:
    """Command-line interface for TypeTrace Backend."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.__db_path = DatabasePath.DB_PATH
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
            from backend.events.windows_darwin import WindowsDarwinEventProcessor

            return WindowsDarwinEventProcessor
        logger.error("Unsupported platform: %s", platform.system())
        return None

    def _initiate_shutdown_callback(self) -> None:
        """Use callback triggered by DbusServiceManager when its loop is stopping."""
        # The primary purpose is fulfilled by DbusServiceManager stopping its own loop.
        # Further shutdown logic occurs after .run() returns in the main thread.
        logger.info("D-Bus service loop stopping callback triggered.")

    def run(self, args: argparse.Namespace) -> int:
        """Run the backend service."""
        if args.debug:
            Config.DEBUG = True
        # Setup logging (using default level if not debug)
        LoggerSetup.setup_logging()

        logger.info("TypeTrace Backend starting...")
        exit_code = ExitCodes.SUCCESS
        processor: BaseEventProcessor | None = None

        try:
            # --- Initialize Database ---
            DatabaseManager.initialize_database(self.__db_path)

            # --- Get and Prepare Processor ---
            processor_class = self._get_processor_class()
            if not processor_class:
                return ExitCodes.PLATFORM_ERROR

            # Check permissions specific to Linux non-Flatpak before instantiating
            if platform.system().lower() == "linux" and not Config.IS_FLATPAK:
                self._check_input_group()  # Can raise PermissionError

            # Instantiate the processor
            processor = processor_class(self.__db_path)

            # Perform accessibility checks if the processor supports it
            if hasattr(processor, "check_device_accessibility"):
                processor.check_device_accessibility()  # Can raise PermissionError

            # --- Start Processor Thread ---
            logger.info("Starting event processor thread...")
            self._processor_thread = threading.Thread(
                target=_run_processor_thread,
                args=(processor,),
                name="EventProcessorThread",
            )
            self._processor_thread.daemon = False  # Must NOT be daemon for clean join
            self._processor_thread.start()

            # --- Start D-Bus Service ---
            logger.info("Initializing D-Bus service manager...")
            self._dbus_manager = DbusServiceManager(
                stop_callback=self._initiate_shutdown_callback,
            )

            # Blocks main thread until D-Bus loop stops (via signal or Quit method)
            dbus_exit_code = self._dbus_manager.run()
            logger.info("D-Bus manager run() finished with code: %d", dbus_exit_code)
            if dbus_exit_code != 0:
                exit_code = (
                    ExitCodes.RUNTIME_ERROR
                )  # Treat D-Bus errors as runtime issues

        # --- Handle Specific Setup Errors ---
        except PermissionError as e:
            logger.exception(
                "Permission error during setup: %s", e, exc_info=Config.DEBUG
            )
            # Ensure thread is cleaned up if it was started before error
            if self._processor_thread and self._processor_thread.is_alive():
                # Cannot easily stop it gracefully here, rely on process exit
                logger.warning("Setup failed after processor thread started.")
            exit_code = ExitCodes.PERMISSION_ERROR
        except sqlite3.Error as e:
            logger.exception(
                "Database error during setup: %s", e, exc_info=Config.DEBUG
            )
            exit_code = ExitCodes.DATABASE_ERROR
        except Exception as e:  # Catch other unexpected setup errors
            logger.critical("Unexpected error during setup: %s", e, exc_info=True)
            exit_code = ExitCodes.RUNTIME_ERROR
        # --- Shutdown Sequence ---
        finally:
            logger.info("Initiating backend shutdown sequence...")

            # If the processor thread was started and is still running...
            # (It might have already stopped if an OS signal terminated both loops)
            if self._processor_thread and self._processor_thread.is_alive():
                # This indicates D-Bus likely stopped internally (e.g., Quit method)
                # or an error occurred after the thread started.
                # Send SIGTERM to the process to trigger the processor's signal handler.
                logger.info(
                    "Processor thread still alive, sending SIGTERM to process %d",
                    os.getpid(),
                )
                try:
                    os.kill(os.getpid(), signal.SIGTERM)
                except Exception:
                    logger.exception("Failed to send SIGTERM to process")

                # Wait for the processor thread to finish
                # Use a reasonable timeout based on buffer flush + reaction time
                join_timeout = getattr(Config, "BUFFER_TIMEOUT", 1.0) * 2 + 5.0
                self._processor_thread.join(timeout=join_timeout)
                if self._processor_thread.is_alive():
                    logger.warning(
                        "Processor thread did not exit cleanly after SIGTERM/timeout."
                    )
            elif self._processor_thread:
                logger.info(
                    "Processor thread already finished when shutdown commenced."
                )

            logger.info("TypeTrace Backend finished.")

        return exit_code

    def _check_input_group(self) -> None:
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
