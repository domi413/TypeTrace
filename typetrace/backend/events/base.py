"""Base class for event processing."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar, final

if TYPE_CHECKING:
    from pathlib import Path

from typetrace.backend.db import DatabaseManager
from typetrace.config import Config, Event

logger = logging.getLogger(__name__)

DeviceType = TypeVar("DeviceType")


class BaseEventProcessor(ABC, Generic[DeviceType]):
    """Abstract base class for event processing."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the processor with a database path."""
        self._db_manager = DatabaseManager()
        self._db_path: Path = db_path

    @abstractmethod
    def trace(self) -> None:
        """Start tracing events."""

    @final
    def _check_timeout_and_flush(
        self,
        buffer: list[Event],
        start_time: float,
        db_path: Path,
        *,
        flush: bool = False,
    ) -> tuple[list[Event], float]:
        """Check if buffer timeout has been reached and flush buffer if needed.

        Args:
            buffer: Current buffer of events
            start_time: Time when the buffer started
            db_path: Path to the database
            flush: Force flushing

        Returns:
            Updated buffer and start time

        """
        current_time: float = time.time()

        if buffer and (
            flush
            or len(buffer) >= Config.BUFFER_SIZE
            or current_time - start_time >= Config.BUFFER_TIMEOUT
        ):
            self._db_manager.write_to_database(db_path, buffer)
            buffer.clear()
            start_time = current_time

        return buffer, start_time

    @final
    def _print_event(self, event: Event) -> None:
        """Print event information if in debug mode.

        Args:
            event: Dictionary containing event details.

        """
        logger.debug(
            '{"event_name": "%s", "key_code": %s}',
            event["name"],
            event["scan_code"],
        )

    @abstractmethod
    def _buffer(self, devices: list[DeviceType]) -> None:
        """Buffer events.

        Args:
            devices: List of input devices to monitor.

        """

    @abstractmethod
    def _process_single_event(self, event: DeviceType) -> Event | None:
        """Process a single input event.

        Args:
            event: Event to process

        Returns:
            Updated buffer and start time

        """
