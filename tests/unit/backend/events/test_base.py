"""Tests for the BaseEventProcessor class in the events backend module."""

from __future__ import annotations

import time
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from typetrace.backend.events.base import BaseEventProcessor
from typetrace.config import Config, Event


class ConcreteBaseEventProcessor(BaseEventProcessor):
    """A concrete implementation of BaseEventProcessor for testing purposes."""

    def trace(self) -> None:
        """Implement the abstract trace method for testing."""

    def _buffer(self, devices: list[str]) -> None:
        """Implement the abstract _buffer method for testing."""

    def _process_single_event(self, event: Event) -> None:
        """Implement the abstract _process_single_event method for testing."""


class TestBaseEventProcessor(unittest.TestCase):
    """Test suite for the BaseEventProcessor class."""

    def setUp(self) -> None:
        """Set up the test environment before each test."""
        self.tmp_path: Path = Path("tests/temp")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.processor: ConcreteBaseEventProcessor = ConcreteBaseEventProcessor(
            self.tmp_path / "test.db",
        )

    def test_init(self) -> None:
        """Test the initialization of BaseEventProcessor."""
        assert self.processor._db_path == self.tmp_path / "test.db"

    def test_check_timeout_and_flush_no_flush(self) -> None:
        """Test _check_timeout_and_flush with no flush condition."""
        buffer: list[Event] = [
            {"scan_code": 1, "name": "a", "date": "2023-10-01"},
        ]
        start_time: float = time.time()

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
            )
            assert new_buffer == buffer
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_with_flush_timeout(self) -> None:
        """Test _check_timeout_and_flush with a flush due to timeout."""
        buffer: list[Event] = [
            {"scan_code": 1, "name": "a", "date": "2023-10-01"},
        ]
        start_time: float = time.time() - Config.BUFFER_TIMEOUT - 1

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(
                self.processor._db_path,
                buffer,
            )

    def test_check_timeout_and_flush_with_flush_size(self) -> None:
        """Test _check_timeout_and_flush with a flush due to buffer size."""
        buffer: list[Event] = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE)
        ]
        start_time: float = time.time()

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(
                self.processor._db_path,
                buffer,
            )

    def test_check_timeout_and_flush_empty_buffer(self) -> None:
        """Test _check_timeout_and_flush with an empty buffer."""
        buffer: list[Event] = []
        start_time: float = time.time()

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
            )
            assert new_buffer == []
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_force_flush(self) -> None:
        """Test _check_timeout_and_flush with a forced flush."""
        buffer: list[Event] = [
            {"scan_code": 1, "name": "a", "date": "2023-10-01"},
        ]
        start_time: float = time.time()

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
                flush=True,
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(
                self.processor._db_path,
                buffer,
            )

    def test_check_timeout_and_flush_almost_full_buffer(self) -> None:
        """Test _check_timeout_and_flush with an almost full buffer."""
        buffer: list[Event] = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE - 1)
        ]
        start_time: float = time.time()

        with patch(
            "typetrace.backend.db.DatabaseManager.write_to_database",
        ) as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer,
                start_time,
                self.processor._db_path,
            )
            assert new_buffer == buffer
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_print_event(self) -> None:
        """Test the _print_event method with a valid event."""
        event: Event = {"scan_code": 1, "name": "a", "date": "2023-10-01"}

        with patch("logging.Logger.debug") as mock_debug:
            self.processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "a",
                1,
                "2023-10-01",
            )

    def test_print_event_missing_keys(self) -> None:
        """Test the _print_event method with an event missing required keys."""
        event: Event = {"scan_code": 1}

        with patch("logging.Logger.debug") as mock_debug:
            with pytest.raises(KeyError):
                self.processor._print_event(event)
            mock_debug.assert_not_called()

    def test_print_event_invalid_values(self) -> None:
        """Test the _print_event method with an event containing invalid values."""
        event: Event = {"scan_code": None, "name": "", "date": ""}

        with patch("logging.Logger.debug") as mock_debug:
            self.processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "",
                None,
                "",
            )


if __name__ == "__main__":
    unittest.main()
