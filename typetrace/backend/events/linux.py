"""Linux-specific event processing."""

from __future__ import annotations

import logging
import select
import signal
import time
from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, final, override

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import FrameType

import evdev
from backend.config import Config, KeyEvent
from backend.db import DatabaseManager
from backend.events.base import BaseEventProcessor

logger = logging.getLogger(__name__)


@final
class LinuxEventProcessor(BaseEventProcessor):
    """Event processor for Linux platform."""

    def __init__(self) -> None:
        """Initialize the processor."""
        super().__init__()
        self.__cached_keyboards: list[evdev.device.InputDevice] | None = None
        self.__db_path: Path
        self.__terminate = False

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
    def trace(self, db_path: Path) -> None:
        """See base class."""
        # Set up signal handler
        self.__setup_signal_handlers()

        with self._managed_devices() as devices:
            if not devices:
                logger.warning("No keyboard devices found")
                return

            self._buffer(devices, db_path)

    @override
    def _buffer(
        self,
        devices: list[evdev.device.InputDevice],
        db_path: Path,
    ) -> None:
        """See base class."""
        self.__db_path = db_path
        buffer: list[KeyEvent] = []
        start_time: float = time.time()
        self.__terminate = False

        try:
            while not self.__terminate:
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
                    self._cached_keyboards = None
                    devices = self._select_keyboards()

        finally:
            if buffer:
                DatabaseManager.write_to_database(db_path, buffer)
                self._cached_keyboards = None
                logger.debug("Flushing %d events to database before exit", len(buffer))

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

                self._print_key(event_data)
                buffer.append(event_data)

            # TODO: Don't think we should call the write_to_database in
            # multiple places This is also not what _process_single_event is
            # meant to do, this is and shouldbe the job of
            # _check_timeout_and_flush
            if len(buffer) >= Config.BUFFER_SIZE:
                DatabaseManager.write_to_database(self.__db_path, buffer)
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
            # Clear the cached keyboards since we have closed them
            self.__cached_keyboards = None

    def _select_keyboards(self) -> list[evdev.device.InputDevice]:
        """Find and return all keyboard devices.

        Returns:
            List of keyboard input devices.

        """
        if self.__cached_keyboards is not None:
            return self.__cached_keyboards

        devices: list[evdev.device.InputDevice] = [
            evdev.device.InputDevice(fn) for fn in evdev.util.list_devices()
        ]
        keyboards: list[evdev.device.InputDevice] = []

        for device in devices:
            if evdev.ecodes.EV_KEY in device.capabilities():
                keyboards.append(device)
                logger.debug(
                    "Found keyboard device: %s, %r",
                    device.name,
                    device.path,
                )

        # Cache the list of keyboards
        self.__cached_keyboards = keyboards
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
            # FIXME: When unplugging devices during runtime, this exception is
            # raised. I think we are good by raising an exception since it
            # should be treated as an error when the keyboard suddenly
            # disappears, but we should recover from this. Since we're already
            # using the time library, an option could be to call the
            # _select_keyboards every 5 seconds.
            logger.exception("Error reading from device")

        return buffer, start_time

    def __setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful termination."""
        signal.signal(signal.SIGTERM, self.__handle_termination_signal)
        signal.signal(signal.SIGINT, self.__handle_termination_signal)

    def __handle_termination_signal(self, signum: int, _: FrameType | None) -> None:
        """Handle termination signals."""
        logger.debug("Received signal %s, shutting down...", signum)
        self.__terminate = True
