"""Device handling for TypeTrace."""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING

import evdev

from typetrace.config import DEBUG

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
                logging.debug("Found keyboard device: %s, %r", device.name, device.path)

    return keyboards
