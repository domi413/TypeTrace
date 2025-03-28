"""Windows and Darwin-specific event processing."""

import logging
import time
from pathlib import Path
from typing import Any, override

from backend.config import Config, Event
from backend.events.base import BaseEventProcessor
from pynput import keyboard

logger = logging.getLogger(__name__)


class WindowsDarwinEventProcessor(BaseEventProcessor):
    """Event processor for Windows and Darwin platforms."""

    @override
    def trace(self, db_path: Path) -> None:
        """See base class."""

    @override
    def _buffer(self, devices: list[Any]) -> None:  # TODO: Add correct type
        """See base class."""
        buffer: list[Event] = []
        start_time: float = time.time()

    @override
    def _process_single_event(
        self, event: Any
    ) -> Event | None:  # TODO: Add correct type
        """See base class."""
