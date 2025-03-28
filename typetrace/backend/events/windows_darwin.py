"""Windows and Darwin-specific event processing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, override

from backend.events.base import BaseEventProcessor

if TYPE_CHECKING:
    from pathlib import Path

    from backend.config import Event

logger = logging.getLogger(__name__)


class WindowsDarwinEventProcessor(BaseEventProcessor):
    """Event processor for Windows and Darwin platforms."""

    @override
    def trace(self, db_path: Path) -> None:
        """See base class."""

    @override
    def _buffer(self, devices: list[Any]) -> None:
        """See base class."""

    @override
    def _process_single_event(
        self,
        event: Any,
    ) -> Event | None:
        """See base class."""
