import pytest
from unittest.mock import patch
import time
from pathlib import Path

from typetrace.backend.events.base import BaseEventProcessor
from typetrace.config import Config


class TestBaseEventProcessor:
    """Test suite for BaseEventProcessor class."""

    @pytest.fixture
    def base_processor(self, tmp_path):
        """Provide a BaseEventProcessor instance with a temporary database path.

        Args:
            tmp_path: Pytest fixture for a temporary directory.

        Returns:
            A concrete instance of BaseEventProcessor.
        """
        class ConcreteBaseEventProcessor(BaseEventProcessor):
            def trace(self):
                pass

            def _buffer(self, devices):
                pass

            def _process_single_event(self, event):
                pass

        return ConcreteBaseEventProcessor(tmp_path / "test.db")

    def test_init(self, base_processor, tmp_path):
        """Test initialization of BaseEventProcessor."""
        assert base_processor._db_path == tmp_path / "test.db"

    def test_check_timeout_and_flush_no_flush(self, base_processor):
        """Test _check_timeout_and_flush when no flush is triggered."""
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path
            )
            assert new_buffer == buffer
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_with_flush_timeout(self, base_processor):
        """Test _check_timeout_and_flush when flush is triggered by timeout."""
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time() - Config.BUFFER_TIMEOUT - 1
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(base_processor._db_path, buffer)

    def test_check_timeout_and_flush_with_flush_size(self, base_processor):
        """Test _check_timeout_and_flush when flush is triggered by buffer size."""
        buffer = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE)
        ]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(base_processor._db_path, buffer)

    def test_check_timeout_and_flush_empty_buffer(self, base_processor):
        """Test _check_timeout_and_flush with an empty buffer."""
        buffer = []
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path
            )
            assert new_buffer == []
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_force_flush(self, base_processor):
        """Test _check_timeout_and_flush with forced flush."""
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path, flush=True
            )
            assert new_buffer == []
            assert new_start_time > start_time
            mock_write.assert_called_once_with(base_processor._db_path, buffer)

    def test_check_timeout_and_flush_almost_full_buffer(self, base_processor):
        """Test _check_timeout_and_flush with buffer just below size limit."""
        buffer = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE - 1)
        ]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = base_processor._check_timeout_and_flush(
                buffer, start_time, base_processor._db_path
            )
            assert new_buffer == buffer
            assert new_start_time == start_time
            mock_write.assert_not_called()

    def test_print_event(self, base_processor):
        """Test _print_event logs a valid event correctly."""
        event = {"scan_code": 1, "name": "a", "date": "2023-10-01"}
        with patch('logging.Logger.debug') as mock_debug:
            base_processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "a", 1, "2023-10-01"
            )

    def test_print_event_missing_keys(self, base_processor):
        """Test _print_event with missing event keys."""
        event = {"scan_code": 1}  # Missing 'name' and 'date'
        with patch('logging.Logger.debug') as mock_debug:
            with pytest.raises(KeyError):
                base_processor._print_event(event)
            mock_debug.assert_not_called()

    def test_print_event_invalid_values(self, base_processor):
        """Test _print_event with invalid event values."""
        event = {"scan_code": None, "name": "", "date": ""}
        with patch('logging.Logger.debug') as mock_debug:
            base_processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "", None, ""
            )