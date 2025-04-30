"""Linux-specific event processing."""

from __future__ import annotations

import logging
import select
import time
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, Callable, final, override

import evdev

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

from backend.events.base import BaseEventProcessor

from typetrace.config import Config, Event

logger = logging.getLogger(__name__)


@final
class LinuxEventProcessor(BaseEventProcessor):
    """Event processor for the Linux platform."""

    def __init__(
        self,
        db_path: Path,
        db_updated_callback: Callable[[], None] | None = None,
    ) -> None:
        """Initialize the Linux event processor."""
        super().__init__(db_path, db_updated_callback)
        self.__stored_devices: list[evdev.device.InputDevice] | None = None

    def check_device_accessibility(self) -> None:
        """Check if the script has access to any input devices.

        Raises:
            PermissionError: If no input devices can be accessed.

        """
        try:
            if not self._select_devices():
                logger.error("No accessible input devices available")
        except PermissionError:
            logger.exception("Failed trying to access input devices")

    @override
    def trace(self) -> None:
        """See base class."""
        with self._managed_devices() as devices:
            if not devices:
                logger.warning("No devices found")
                return

            self._buffer(devices)

    @override
    def _buffer(self, devices: list[evdev.device.InputDevice]) -> None:
        """See base class."""
        buffer: list[Event] = []
        start_time: float = time.time()

        try:
            while not self._terminate:
                # Wait for events with timeout
                r: list[evdev.device.InputDevice]
                r, _, _ = select.select(devices, [], [], Config.BUFFER_TIMEOUT)

                buffer, start_time = self._check_timeout_and_flush(
                    buffer,
                    start_time,
                    self._db_path,
                )

                # Process events from ready devices
                for device in r:
                    buffer = self._read_device_events(device, buffer)

                # If we had device errors, refresh devices list
                if not devices:
                    self.__stored_devices = None
                    devices = self._select_devices()
        finally:
            logger.debug("Flushing %d events to database before exit", len(buffer))

            self._check_timeout_and_flush(
                buffer,
                start_time,
                self._db_path,
                flush=True,
            )

    @override
    def _process_single_event(self, event: evdev.events.InputEvent) -> Event | None:
        """See base class."""
        # Trigger on press
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
                event_data: Event = {
                    "scan_code": event.code,
                    "name": event_map[event.code],
                    "date": self._current_date,
                }
                self._print_event(event_data)

                return event_data
        return None

    @contextmanager
    def _managed_devices(self) -> Generator[list[evdev.device.InputDevice], None, None]:
        """Context manager for handling devices.

        Yields:
            List of input devices.

        """
        devices: list[evdev.device.InputDevice] = self._select_devices()
        try:
            yield devices
        finally:
            # Close all devices on exit
            for device in devices:
                with suppress(Exception):
                    device.close()
            # Clear the cached devices since we have closed them
            self.__stored_devices = None

    def _select_devices(self) -> list[evdev.device.InputDevice]:
        """Find and return all devices.

        Returns:
            List of input devices.

        """
        if self.__stored_devices is not None:
            return self.__stored_devices

        devices: list[evdev.device.InputDevice] = [
            evdev.device.InputDevice(fp) for fp in evdev.util.list_devices()
        ]

        if logging.DEBUG:
            for device in devices:
                if evdev.ecodes.EV_KEY in device.capabilities():
                    logger.debug(
                        "Found keyboard device: %s, %r",
                        device.name,
                        device.path,
                    )

        # Cache the list of devices
        self.__stored_devices = devices
        return devices

    def _read_device_events(
        self,
        device: evdev.device.InputDevice,
        buffer: list[Event],
    ) -> list[Event]:
        """Read events from a single device.

        Args:
            device: Input device to read from
            buffer: Current buffer of events
            start_time: Time when the buffer started

        Returns:
            Updated buffer and start time

        """
        try:
            for event in device.read():
                processed_event = self._process_single_event(event)
                if processed_event is not None:
                    buffer.append(processed_event)
        except OSError:
            logger.exception("Error reading from device")

        return buffer
