"""Device handling for TypeTrace."""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING

import evdev
from backend.config import DEBUG

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def managed_devices() -> Generator[list[evdev.device.InputDevice], None, None]:
    """Context manager for handling keyboard devices.

    Yields:
        List of keyboard input devices.

    """
    devices: list[evdev.device.InputDevice] = select_keyboards()
    try:
        yield devices
    finally:
        # Close all devices on exit
        for device in devices:
            with suppress(Exception):
                device.close()


def select_keyboards() -> list[evdev.device.InputDevice]:
    """Find and return all keyboard devices.

    Returns:
        List of keyboard input devices.

    """
    devices: list[evdev.device.InputDevice] = [
        evdev.device.InputDevice(fn) for fn in evdev.util.list_devices()
    ]
    keyboards: list[evdev.device.InputDevice] = []

    for device in devices:
        if evdev.ecodes.EV_KEY in device.capabilities():
            keyboards.append(device)
            if DEBUG:
                logger.debug("Found keyboard device: %s, %r", device.name, device.path)

    return keyboards


def check_device_accessibility() -> None:
    """Check if the script has access to any input devices.

    Raises:
        PermissionError: If no input devices can be accessed.

    """
    try:
        if not select_keyboards():
            logger.exception("No accessible input devices available")

    except PermissionError:
        logger.exception("Failed trying to access input devices")
