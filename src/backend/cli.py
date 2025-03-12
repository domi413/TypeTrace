"""Command-line interface for TypeTrace."""

from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path

import appdirs
from backend.config import DB_NAME, PROJECT_NAME, PROJECT_VERSION, ExitCodes


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


def resolve_db_path() -> Path:
    """Determine the database path following XDG Base Directory specs."""
    xdg_data_home: str = os.getenv(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    db_dir: Path = Path(xdg_data_home) / "typetrace"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / DB_NAME


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
        from backend.devices import check_device_accessibility

        check_device_accessibility()
        db_path: Path = resolve_db_path()

        from backend.db import initialize_database

        initialize_database(db_path)

        from backend.events import trace_keys

        trace_keys(db_path)
    except PermissionError:
        logging.exception(
            "\nPlease ensure you have sufficient permissions (e.g., 'input' group)."
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
