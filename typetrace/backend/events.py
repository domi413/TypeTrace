"""Event processing for TypeTrace."""

from __future__ import annotations

import logging
import select
import signal
import sys
import time
from typing import TYPE_CHECKING

import evdev
from backend.config import BUFFER_SIZE, BUFFER_TIMEOUT, DEBUG, EventData, KeyEvent, MouseEvent
from backend.db import write_to_database
from backend.devices import select_keyboards

if TYPE_CHECKING:
    from pathlib import Path


logger = logging.getLogger(__name__)

_buffer = []
_db_path = None


def signal_handler(sig_num, frame):
    """Signal handler for graceful termination."""
    logger.debug("Received signal %d, shutting down gracefully...", sig_num)
    global _buffer, _db_path
    if _buffer:
        write_to_database(_db_path, _buffer)
    sys.exit(0)


def print_key(event: KeyEvent) -> None:
    """Print key information if in debug mode.

    Args:
        event: Dictionary containing key details.

    """
    logger.debug(
        '{"key_name": "%s", "key_code": %s}',
        event["name"],
        event["scan_code"],
    )


def print_mouse_position(event: MouseEvent) -> None:
    """Print mouse position information if in debug mode.

    Args:
        event: Dictionary containing mouse position details.

    """
    logger.debug(
        '{"mouse_pos_type": "%s", "x": %d, "y": %d}',
        event["type"],
        event["x"],
        event["y"],
    )


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Track absolute mouse position - initialize to center of screen
_mouse_x = 0
_mouse_y = 0


def process_single_event(
    event: evdev.events.InputEvent,
    buffer: list[EventData],
    start_time: float,
    db_path: Path,
) -> tuple[list[EventData], float]:
    """Process a single keyboard or mouse event.

    Args:
        event: Evdev event to process
        buffer: Current buffer of key and mouse events
        start_time: Time when the buffer started
        db_path: Path to the database

    Returns:
        Updated buffer and start time
    """

    # Capture event timestamp
    event_time = event.timestamp()
    global _mouse_x, _mouse_y

    # Process keyboard events (Trigger on keypress)
    if event.type == evdev.ecodes.EV_KEY and event.value == 1:
        event_map: dict[int, str | tuple[str]] | None = None
        event_code: int = event.code

        # Keyboard input
        if event_code in evdev.ecodes.KEY:
            event_map = evdev.ecodes.KEY
        # Mouse input
        elif event_code in evdev.ecodes.BTN:
            event_map = evdev.ecodes.BTN

        if event_map is not None:
            event_data: KeyEvent = {
                "scan_code": event.code,
                "name": event_map[event.code],
            }

        if event_map is not None:
            event_data: KeyEvent = {
                "scan_code": event.code,
                "name": event_map[event.code],
            }

            if DEBUG:
                print_key(event_data)

            buffer.append(event_data)

    # Touchpad
    elif event.type == evdev.ecodes.EV_ABS:
        if event.code == evdev.ecodes.ABS_X:
            _mouse_x = event.value
            # Clamp to screen boundaries
            _mouse_x = max(0, min(_mouse_x, SCREEN_WIDTH))

        elif event.code == evdev.ecodes.ABS_Y:
            _mouse_y = event.value
            # Clamp to screen boundaries
            _mouse_y = max(0, min(_mouse_y, SCREEN_HEIGHT))

        if DEBUG:
            logger.debug("X/Y: %d, %d", _mouse_x, _mouse_y)

    # Mouse
    elif event.type == evdev.ecodes.EV_REL:
        if event.code == evdev.ecodes.REL_X:
            _mouse_x += event.value
            # Clamp to screen boundaries
            _mouse_x = max(0, min(_mouse_x, SCREEN_WIDTH))

        elif event.code == evdev.ecodes.REL_Y:
            _mouse_y += event.value
            # Clamp to screen boundaries
            _mouse_y = max(0, min(_mouse_y, SCREEN_HEIGHT))

        if DEBUG:
            logger.debug("X/Y: %d, %d", _mouse_x, _mouse_y)

    if len(buffer) >= BUFFER_SIZE:
        write_to_database(db_path, _buffer)
        buffer.clear()
        start_time = time.time()

    return buffer, start_time


def read_device_events(
    device: evdev.device.InputDevice,
    buffer: list[KeyEvent],
    start_time: float,
    db_path: Path,
) -> tuple[list[KeyEvent], float]:
    """Read events from a single device.

    Args:
        device: Input device to read from
        buffer: Current buffer of key events
        start_time: Time when the buffer started
        db_path: Path to the database

    Returns:
        Updated buffer and start time

    """
    try:
        for event in device.read():
            buffer, start_time = process_single_event(
                event,
                buffer,
                start_time,
                db_path,
            )
    except OSError:
        logger.exception("Error reading from device")
        # We'll handle device reconnection in the main loop

    return buffer, start_time


def check_timeout_and_flush(
    buffer: list[KeyEvent],
    start_time: float,
    db_path: Path,
) -> tuple[list[KeyEvent], float]:
    """Check if buffer timeout has been reached and flush buffer if needed.

    Args:
        buffer: Current buffer of key events
        start_time: Time when the buffer started
        db_path: Path to the database

    Returns:
        Updated buffer and start time

    """
    if buffer and time.time() - start_time >= BUFFER_TIMEOUT:
        write_to_database(db_path, buffer)
        buffer.clear()
        start_time = time.time()

    return buffer, start_time


def buffer_keys(devices: list[evdev.device.InputDevice], db_path: Path) -> None:
    """Buffer up to BUFFER_SIZE keystrokes or until BUFFER_TIMEOUT, then write them.

    Args:
        devices: List of keyboard input devices to monitor.
        db_path: Path to the database.

    """
    global _buffer, _db_path
    _buffer = []
    _db_path = db_path
    start_time: float = time.time()

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        # Wait for events with timeout
        r: list[evdev.device.InputDevice]
        r, _, _ = select.select(devices, [], [], BUFFER_TIMEOUT)

        # If no events but timeout reached
        if not r:
            buffer, start_time = check_timeout_and_flush(
                _buffer,
                start_time,
                db_path,
            )
            continue

        # Process events from ready devices
        for device in r:
            buffer, start_time = read_device_events(
                device,
                _buffer,
                start_time,
                db_path,
            )

        # If we had device errors, refresh devices list
        if not devices:
            devices = select_keyboards()


def trace_keys(db_path: Path) -> None:
    """Start tracing keyboard events."""
    from backend.devices import managed_devices

    with managed_devices() as devices:
        if not devices:
            logger.warning("No keyboard devices found")
            return

        buffer_keys(devices, db_path)
