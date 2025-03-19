"""Command-line interface for TypeTrace."""

from __future__ import annotations

import grp
import logging
import os
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import appdirs
from backend.config import DB_NAME, PROJECT_NAME, ExitCodes

if TYPE_CHECKING:
    import argparse

logger = logging.getLogger(__name__)


def resolve_db_path() -> Path:
    """Determine the database path using appdirs for cross-platform support."""
    app_name = PROJECT_NAME.lower()
    data_dir = appdirs.user_data_dir(app_name)
    db_path = Path(data_dir) / DB_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    return db_path


def check_input_group() -> None:
    """Check if the current user is in the 'input' group."""
    username = os.getlogin()
    input_group = grp.getgrnam("input")
    if username not in input_group.gr_mem:
        logger.error("The User %s is not in the 'input' group", username)
        raise PermissionError


def main(args: argparse.Namespace) -> int:
    """Run the main logic of the TypeTrace backend.

    Returns:
        Exit code for the application.

    """
    if args.debug:
        # Update the global DEBUG variable
        import backend.config

        backend.config.DEBUG = True
        from backend.logging_setup import setup_logging

        setup_logging()

    try:
        check_input_group()

        from backend.devices import check_device_accessibility

        check_device_accessibility()
        db_path: Path = resolve_db_path()

        from backend.db import initialize_database

        initialize_database(db_path)

        from backend.events import trace_keys

        trace_keys(db_path)
    except PermissionError:
        return ExitCodes.PERMISSION_ERROR
    except sqlite3.Error:
        logger.exception("Database error")
        return ExitCodes.DATABASE_ERROR
    except (OSError, ValueError, RuntimeError):
        logger.exception("Unexpected error")
        return ExitCodes.RUNTIME_ERROR
    else:
        return ExitCodes.SUCCESS
