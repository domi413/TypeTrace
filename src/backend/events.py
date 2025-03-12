"""Event processing for TypeTrace."""

from __future__ import annotations

import logging
import select
import time

import evdev

from pathlib import Path
from backend.config import BUFFER_SIZE, BUFFER_TIMEOUT, DEBUG, KeyEvent
from backend.db import write_to_database
from backend.devices import select_keyboards


def print_key(event: KeyEvent) -> None:
    """Print key information if in debug mode.

    Args:
        event: Dictionary containing key details.

    """
    logging.debug(
        '{"key_name": "%s", "key_code": %s}',
        event["name"],
        event["scan_code"],
    )


def process_single_event(
    event: evdev.events.InputEvent,
    buffer: list[KeyEvent],
    start_time: float,
    db_path: Path,
) -> tuple[list[KeyEvent], float]:
    """Process a single keyboard event.

    Args:
        event: Evdev event to process
        buffer: Current buffer of key events
        start_time: Time when the buffer started

    Returns:
        Updated buffer and start time

    """
    # Trigger on keypress
    if event.type == evdev.ecodes.EV_KEY and event.value == 1:
        # Ignore unknown keycodes (e.g. mouse input)
        if event.code in evdev.ecodes.KEY:
            key_event: KeyEvent = {
                "scan_code": event.code,
                "name": evdev.ecodes.KEY[event.code],
            }

            if DEBUG:
                print_key(key_event)

            buffer.append(key_event)

        if len(buffer) >= BUFFER_SIZE:
            write_to_database(db_path, buffer)
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

    Returns:
        Updated buffer and start time

    """
    try:
        for event in device.read():
            buffer, start_time = process_single_event(event, buffer, start_time, db_path)
    except OSError:
        logging.exception("Error reading from device")
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

    """
    buffer: list[KeyEvent] = []
    start_time: float = time.time()

    try:
        while True:
            # Wait for events with timeout
            r: list[evdev.device.InputDevice]
            r, _, _ = select.select(devices, [], [], BUFFER_TIMEOUT)

            # If no events but timeout reached
            if not r:
                buffer, start_time = check_timeout_and_flush(buffer, start_time, db_path)
                continue

            # Process events from ready devices
            for device in r:
                buffer, start_time = read_device_events(device, buffer, start_time, db_path)

            # If we had device errors, refresh devices list
            if not devices:
                devices = select_keyboards()

    except KeyboardInterrupt:
        if buffer:
            write_to_database(db_path, buffer)


def trace_keys(db_path: Path) -> None:
    """Start tracing keyboard events."""
    from backend.devices import managed_devices

    with managed_devices() as devices:
        if not devices:
            logging.warning("No keyboard devices found")
            return

        buffer_keys(devices, db_path)
