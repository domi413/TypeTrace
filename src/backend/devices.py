"""Device handling for TypeTrace."""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, List

import evdev

from backend.config import DEBUG

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

def check_device_accessibility() -> None:
    """Check if the script has access to any input devices.

    Raises:
        PermissionError: If no input devices can be accessed.
    """
    try:
        device_paths = evdev.list_devices()
        if not device_paths:
            raise PermissionError("No input devices found.")

        accessible_devices: List[evdev.InputDevice] = []
        for path in device_paths:
            try:
                dev = evdev.InputDevice(path)
                accessible_devices.append(dev)
                # Close the device to avoid keeping it open unnecessarily
                dev.close()
            except PermissionError:
                # Skip devices we can't access (e.g., restricted by ACLs or group)
                continue

        if not accessible_devices:
            raise PermissionError("No accessible input devices available.")
        # At least one device is accessible; no need to keep them open here
    except Exception as e:
        raise PermissionError(f"Failed trying to access input devices: {e}")
