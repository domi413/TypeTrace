"""Base class for event processing."""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, final

from backend.config import Config, KeyEvent
from backend.db import DatabaseManager

logger = logging.getLogger(__name__)


class BaseEventProcessor(ABC):
    """Abstract base class for event processing."""

    @abstractmethod
    def trace(self, db_path: Path) -> None:
        """Start tracing keyboard events."""

    @final
    def _check_timeout_and_flush(
        self,
        buffer: list[KeyEvent],
        start_time: float,
        db_path: Path,
    ) -> tuple[list[KeyEvent], float]:
        """Check if buffer timeout has been reached and flush buffer if needed.

        Args:
            buffer: Current buffer of events
            start_time: Time when the buffer started
            db_path: Path to the database

        Returns:
            Updated buffer and start time

        """
        if buffer and time.time() - start_time >= Config.BUFFER_TIMEOUT:
            DatabaseManager.write_to_database(db_path, buffer)
            buffer.clear()
            start_time = time.time()

        return buffer, start_time

    @final
    def _print_key(self, event: KeyEvent) -> None:
        """Print key information if in debug mode.

        Args:
            event: Dictionary containing key details.

        """
        logger.debug(
            '{"key_name": "%s", "key_code": %s}',
            event["name"],
            event["scan_code"],
        )

    @abstractmethod
    def _buffer(self, devices: list[Any], db_path: Path) -> None:
        """Buffer up to BUFFER_SIZE or until BUFFER_TIMEOUT, then write them.

        Buffer will be flushed by calling _check_timeout_and_flush.

        Args:
            devices: List of input devices to monitor.
            db_path: Path to the database.

        """

    @abstractmethod
    def _process_single_event(
        self,
        event: Any,
        buffer: list[KeyEvent],
        start_time: float,
    ) -> tuple[list[KeyEvent], float]:
        """Process a single input event.

        Args:
            event: Event to process
            buffer: Current buffer of events
            start_time: Time when the buffer started

        Returns:
            Updated buffer and start time

        """
