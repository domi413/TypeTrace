"""Command-line interface for TypeTrace."""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
from pathlib import Path

from backend.config import DB_NAME, PROJECT_VERSION, ExitCodes


def check_root_permissions() -> None:
    """Check if the script is running with root permissions.

    Raises:
        PermissionError: If the script is not running with root permissions.

    """
    if os.geteuid() != 0:
        raise PermissionError


def print_help() -> None:
    """Display help information."""
    print("The backend of TypeTrace.")
    print(f"Version: {PROJECT_VERSION}")
    print("\nUsage: sudo python -m typetrace [OPTION...]")
    print("Options:")
    print("\t-h, --help\tDisplay help then exit.")
    print("\t-v, --version\tDisplay version then exit.")
    print("\t-d, --debug\tEnable debug mode.")
    print(
        "\nWarning: This is the backend and is not designed to run by users.",
        "\nYou should run the frontend of TypeTrace which will run this.",
    )


def main() -> int:
    """Run the main logic of the TypeTrace backend.

    Returns:
        Exit code for the application.

    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")

    args = parser.parse_args()
    if args.help:
        print_help()
        return ExitCodes.SUCCESS

    if args.version:
        print(PROJECT_VERSION)
        return ExitCodes.SUCCESS

    if args.debug:
        # Update the global DEBUG variable
        import backend.config

        backend.config.DEBUG = True
        from backend.logging_setup import setup_logging

        setup_logging()

    try:
        check_root_permissions()
        db_path: Path = Path(DB_NAME).resolve()
        from backend.db import initialize_database

        initialize_database(db_path)
        from backend.events import trace_keys

        trace_keys()
    except PermissionError:
        print(
            "Permission denied when accessing input devices.",
            "\nPlease run this script with sudo or adjust permissions.",
        )
        return ExitCodes.PERMISSION_ERROR
    except sqlite3.Error:
        logging.exception("Database error")
        return ExitCodes.DATABASE_ERROR
    except (OSError, ValueError, RuntimeError):
        logging.exception("Unexpected error")
        return ExitCodes.RUNTIME_ERROR
    else:
        return ExitCodes.SUCCESS
