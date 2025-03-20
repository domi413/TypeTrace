"""Command-line interface for TypeTrace."""

from __future__ import annotations

import argparse
import grp
import logging
import os
import select
import sqlite3
from pathlib import Path

import appdirs
import evdev
from backend.config import DB_NAME, PROJECT_NAME, PROJECT_VERSION, ExitCodes

logger = logging.getLogger(__name__)


def print_help() -> None:
    """Display help information."""
    print("The backend of TypeTrace.")
    print(f"Version: {PROJECT_VERSION}")
    print("\nUsage: sudo python -m typetrace [OPTION...]")
    print("Options:")
    print("\t-h, --help\tDisplay help then exit.")
    print("\t-v, --version\tDisplay version then exit.")
    print("\t-d, --debug\tEnable debug mode.")
    print("\t-c, --calibrate\tCalibrate screen dimensions for mouse tracking.")
    print(
        "\nWarning: This is the backend and is not designed to run by users.",
        "\nYou should run the frontend of TypeTrace which will run this.",
    )


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


def calibrate_screen_size(devices: list) -> tuple[int, int]:
    """Calibrate the screen size by having the user click at screen corners.

    Args:
        devices: List of input devices to monitor

    Returns:
        Tuple with (screen_width, screen_height) in pixels

    """
    print("\n===== SCREEN CALIBRATION =====")
    print("This will calibrate your screen dimensions for accurate mouse tracking.")
    print("1. Move your mouse to the UPPER-LEFT corner of your screen (0,0)")
    print("2. Click the left mouse button")

    # Reset mouse tracking to make this the origin (0,0)
    global _mouse_x, _mouse_y
    _mouse_x = 0
    _mouse_y = 0

    # Get the first corner - we'll consider this (0,0)
    wait_for_mouse_click(devices)
    print("Origin point set to (0,0)")

    print("3. Now move your mouse to the BOTTOM-RIGHT corner of your screen")
    print("4. Click the left mouse button")

    # Get the second corner - this will be our max coordinates
    corner2 = wait_for_mouse_click(devices)

    # The second click gives us the screen dimensions directly
    width = corner2[0]  # xmax
    height = corner2[1]  # ymax

    print(f"Calibration complete! Screen dimensions: {width}x{height} pixels")
    print(f"Coordinate space: (0,0) to ({width},{height})")

    return width, height


def wait_for_mouse_click(devices: list) -> tuple[int, int]:
    """Wait for the user to click the left mouse button and return position.

    Args:
        devices: List of input devices to monitor

    Returns:
        Tuple with (x, y) coordinates

    """
    from backend.events import _mouse_x, _mouse_y

    print("Waiting for mouse click...")

    while True:
        # Wait for events with a timeout
        r, _, _ = select.select(devices, [], [], 0.1)

        for device in r:
            try:
                for event in device.read():
                    # Process movement events to update position
                    if event.type == evdev.ecodes.EV_REL:
                        if event.code == evdev.ecodes.REL_X:
                            _mouse_x += event.value
                        elif event.code == evdev.ecodes.REL_Y:
                            _mouse_y += event.value

                    # Process absolute movement events for touchpads
                    elif event.type == evdev.ecodes.EV_ABS:
                        if event.code == evdev.ecodes.ABS_X:
                            _mouse_x = event.value
                        elif event.code == evdev.ecodes.ABS_Y:
                            _mouse_y = event.value

                    # Check for left mouse button click
                    if (
                        event.type == evdev.ecodes.EV_KEY
                        and event.code == evdev.ecodes.BTN_LEFT
                        and event.value == 1
                    ):
                        print(f"Click detected at coordinates: ({_mouse_x}, {_mouse_y})")
                        return (_mouse_x, _mouse_y)
            except Exception as e:
                logger.error(f"Error reading device events during calibration: {e}")


def main() -> int:
    """Run the main logic of the TypeTrace backend.

    Returns:
        Exit code for the application.

    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-c", "--calibrate", action="store_true")

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
        check_input_group()

        from backend.devices import check_device_accessibility

        check_device_accessibility()
        db_path: Path = resolve_db_path()

        from backend.db import initialize_database

        initialize_database(db_path)

        from backend.devices import managed_devices

        with managed_devices() as devices:
            if not devices:
                logger.warning("No input devices found")
                return ExitCodes.RUNTIME_ERROR

            # Perform screen calibration
            if args.calibrate:
                # Import and update the global variables in the events module
                import backend.events

                width, height = calibrate_screen_size(devices)
                backend.events.SCREEN_WIDTH = width
                backend.events.SCREEN_HEIGHT = height

                print(f"Screen dimensions set to: {width}x{height}")

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
