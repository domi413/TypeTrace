"""Base class for event processing."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    from pathlib import Path

from backend.config import Config, Event
from backend.db import DatabaseManager

logger = logging.getLogger(__name__)


class BaseEventProcessor(ABC):
    """Abstract base class for event processing."""

    @abstractmethod
    def trace(self, db_path: Path) -> None:
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

        if (
            flush
            or len(buffer) >= Config.BUFFER_SIZE
            or current_time - start_time >= Config.BUFFER_TIMEOUT
        ):
            DatabaseManager.write_to_database(db_path, buffer)
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
    def _buffer(self, devices: list[Any]) -> None:
        """Buffer events.

        Args:
            devices: List of input devices to monitor.

        """

    @abstractmethod
    def _process_single_event(self, event: Any) -> Event | None:
        """Process a single input event.

        Args:
            event: Event to process

        Returns:
            Updated buffer and start time

        """
