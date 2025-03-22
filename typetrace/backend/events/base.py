"""Base class for event processing."""

from pathlib import Path
from typing import List


class BaseEventProcessor:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def process_events(self):
        raise NotImplementedError(
            "Method 'process_events' must be implemented in subclasses"
        )

