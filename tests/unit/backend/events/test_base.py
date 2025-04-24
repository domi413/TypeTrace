import unittest
from unittest.mock import patch
import time
from pathlib import Path

from typetrace.backend.events.base import BaseEventProcessor
from typetrace.config import Config


class ConcreteBaseEventProcessor(BaseEventProcessor):
    def trace(self):
        pass

    def _buffer(self, devices):
        pass

    def _process_single_event(self, event):
        pass


class TestBaseEventProcessor(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path("tests/temp")  # alternativ: tempfile.TemporaryDirectory + Pathlib
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        self.processor = ConcreteBaseEventProcessor(self.tmp_path / "test.db")

    def test_init(self):
        self.assertEqual(self.processor._db_path, self.tmp_path / "test.db")

    def test_check_timeout_and_flush_no_flush(self):
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path
            )
            self.assertEqual(new_buffer, buffer)
            self.assertEqual(new_start_time, start_time)
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_with_flush_timeout(self):
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time() - Config.BUFFER_TIMEOUT - 1
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path
            )
            self.assertEqual(new_buffer, [])
            self.assertGreater(new_start_time, start_time)
            mock_write.assert_called_once_with(self.processor._db_path, buffer)

    def test_check_timeout_and_flush_with_flush_size(self):
        buffer = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE)
        ]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path
            )
            self.assertEqual(new_buffer, [])
            self.assertGreater(new_start_time, start_time)
            mock_write.assert_called_once_with(self.processor._db_path, buffer)

    def test_check_timeout_and_flush_empty_buffer(self):
        buffer = []
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path
            )
            self.assertEqual(new_buffer, [])
            self.assertEqual(new_start_time, start_time)
            mock_write.assert_not_called()

    def test_check_timeout_and_flush_force_flush(self):
        buffer = [{"scan_code": 1, "name": "a", "date": "2023-10-01"}]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path, flush=True
            )
            self.assertEqual(new_buffer, [])
            self.assertGreater(new_start_time, start_time)
            mock_write.assert_called_once_with(self.processor._db_path, buffer)

    def test_check_timeout_and_flush_almost_full_buffer(self):
        buffer = [
            {"scan_code": i, "name": f"key_{i}", "date": "2023-10-01"}
            for i in range(Config.BUFFER_SIZE - 1)
        ]
        start_time = time.time()
        with patch('typetrace.backend.db.DatabaseManager.write_to_database') as mock_write:
            new_buffer, new_start_time = self.processor._check_timeout_and_flush(
                buffer, start_time, self.processor._db_path
            )
            self.assertEqual(new_buffer, buffer)
            self.assertEqual(new_start_time, start_time)
            mock_write.assert_not_called()

    def test_print_event(self):
        event = {"scan_code": 1, "name": "a", "date": "2023-10-01"}
        with patch('logging.Logger.debug') as mock_debug:
            self.processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "a", 1, "2023-10-01"
            )

    def test_print_event_missing_keys(self):
        event = {"scan_code": 1}
        with patch('logging.Logger.debug') as mock_debug:
            with self.assertRaises(KeyError):
                self.processor._print_event(event)
            mock_debug.assert_not_called()

    def test_print_event_invalid_values(self):
        event = {"scan_code": None, "name": "", "date": ""}
        with patch('logging.Logger.debug') as mock_debug:
            self.processor._print_event(event)
            mock_debug.assert_called_once_with(
                '{"event_name": "%s", "key_code": %s, "date": "%s"}',
                "", None, ""
            )


if __name__ == "__main__":
    unittest.main()
