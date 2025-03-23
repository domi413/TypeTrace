"""Linux-specific event processing."""

import logging
import select
import time
from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import final, override

import evdev

from typetrace.backend.config import Config, KeyEvent
from typetrace.backend.db import DatabaseManager
from typetrace.backend.events.base import BaseEventProcessor

logger = logging.getLogger(__name__)


@final
class LinuxEventProcessor(BaseEventProcessor):
    """Event processor for Linux platform."""

    def check_device_accessibility(self) -> None:
        """Check if the script has access to any input devices.

        Raises:
            PermissionError: If no input devices can be accessed.

        """
        try:
            if not self._select_keyboards():
                logger.error("No accessible input devices available")
        except PermissionError:
            logger.exception("Failed trying to access input devices")

    @override
    def trace_keys(self, db_path: Path) -> None:
        """See base class."""
        with self._managed_devices() as devices:
            if not devices:
                logger.warning("No keyboard devices found")
                return

            self._buffer_keys(devices, db_path)

    @override
    def _buffer_keys(
        self,
        devices: list[evdev.device.InputDevice],
        db_path: Path,
    ) -> None:
        """See base class."""
        self._db_path = db_path
        buffer: list[KeyEvent] = []
        start_time: float = time.time()

        try:
            while True:
                # Wait for events with timeout
                r: list[evdev.device.InputDevice]
                r, _, _ = select.select(devices, [], [], Config.BUFFER_TIMEOUT)

                # If no events but timeout reached
                if not r:
                    buffer, start_time = self._check_timeout_and_flush(
                        buffer,
                        start_time,
                        db_path,
                    )
                    continue

                # Process events from ready devices
                for device in r:
                    buffer, start_time = self._read_device_events(
                        device,
                        buffer,
                        start_time,
                    )

                # If we had device errors, refresh devices list
                if not devices:
                    devices = self._select_keyboards()

        except KeyboardInterrupt:
            if buffer:
                DatabaseManager.write_to_database(db_path, buffer)

    @override
    def _process_single_event(
        self,
        event: evdev.events.InputEvent,
        buffer: list[KeyEvent],
        start_time: float,
    ) -> tuple[list[KeyEvent], float]:
        """See base class."""
        # Trigger on keypress
        if event.type == evdev.ecodes.EV_KEY and event.value == 1:
            event_map: dict[int, str | tuple[str]] | None = None
            event_code: int = event.code

            # Keyboard input
            if event_code in evdev.ecodes.KEY:
                event_map = evdev.ecodes.KEY
            # Mouse input
            # elif event_code in evdev.ecodes.BTN:  # noqa: ERA001
            #     event_map = evdev.ecodes.BTN  # noqa: ERA001

            if event_map is not None:
                event_data: KeyEvent = {
                    "scan_code": event.code,
                    "name": event_map[event.code],
                }

                if Config.DEBUG:
                    self._print_key(event_data)

                buffer.append(event_data)

            if len(buffer) >= Config.BUFFER_SIZE:
                DatabaseManager.write_to_database(self._db_path, buffer)
                buffer.clear()
                start_time = time.time()

        return buffer, start_time

    @contextmanager
    def _managed_devices(self) -> Generator[list[evdev.device.InputDevice], None, None]:
        """Context manager for handling keyboard devices.

        Yields:
            List of keyboard input devices.

        """
        devices: list[evdev.device.InputDevice] = self._select_keyboards()
        try:
            yield devices
        finally:
            # Close all devices on exit
            for device in devices:
                with suppress(Exception):
                    device.close()

    def _select_keyboards(self) -> list[evdev.device.InputDevice]:
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
                if Config.DEBUG:
                    logger.debug(
                        "Found keyboard device: %s, %r",
                        device.name,
                        device.path,
                    )

        return keyboards

    def _read_device_events(
        self,
        device: evdev.device.InputDevice,
        buffer: list[KeyEvent],
        start_time: float,
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
                buffer, start_time = self._process_single_event(
                    event,
                    buffer,
                    start_time,
                )
        except OSError:
            logger.exception("Error reading from device")

        return buffer, start_time
