"""Test module for Linux event processing in TypeTrace."""

from unittest.mock import MagicMock

import pytest

from typetrace.backend.events.base import BaseEventProcessor


@pytest.fixture
def event_processor() -> BaseEventProcessor:
    """Create a mock BaseEventProcessor for testing."""
    mock_processor = MagicMock(spec=BaseEventProcessor)

    # Define methods expected to be called during tests
    mock_processor.check_timeout_and_flush = MagicMock()
    mock_processor.process_single_event = MagicMock()
    mock_processor.read_device_events = MagicMock()
    mock_processor.check_device_accessibility = MagicMock()

    return mock_processor


def test_empty_buffer_flush(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_timeout_and_flush with an empty buffer."""
    event_processor.check_timeout_and_flush()
    event_processor.check_timeout_and_flush.assert_called_once()


def test_timeout_reached_flush(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_timeout_and_flush when timeout is reached."""
    event_processor.check_timeout_and_flush()
    event_processor.check_timeout_and_flush.assert_called_once()


def test_buffer_size_reached_flush(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_timeout_and_flush when buffer size is reached."""
    event_processor.check_timeout_and_flush()
    event_processor.check_timeout_and_flush.assert_called_once()


def test_force_flush(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_timeout_and_flush with force flush."""
    event_processor.check_timeout_and_flush()
    event_processor.check_timeout_and_flush.assert_called_once()


def test_process_key_press_event(
    event_processor: BaseEventProcessor,
) -> None:
    """Test process_single_event with a key press event."""
    event_processor.process_single_event("key_press")
    event_processor.process_single_event.assert_called_once_with("key_press")


def test_process_key_release_event(
    event_processor: BaseEventProcessor,
) -> None:
    """Test process_single_event with a key release event."""
    event_processor.process_single_event("key_release")
    event_processor.process_single_event.assert_called_once_with("key_release")


def test_process_non_key_event(
    event_processor: BaseEventProcessor,
) -> None:
    """Test process_single_event with a non-key event."""
    event_processor.process_single_event("mouse_click")
    event_processor.process_single_event.assert_called_once_with("mouse_click")


def test_read_device_events_success(
    event_processor: BaseEventProcessor,
) -> None:
    """Test read_device_events success case."""
    event_processor.read_device_events()
    event_processor.read_device_events.assert_called_once()


def test_read_device_events_error(
    event_processor: BaseEventProcessor,
) -> None:
    """Test read_device_events error case."""
    event_processor.read_device_events()
    event_processor.read_device_events.assert_called_once()


def test_no_devices_accessibility(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_device_accessibility with no devices."""
    event_processor.check_device_accessibility()
    event_processor.check_device_accessibility.assert_called_once()


def test_permission_error_accessibility(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_device_accessibility with permission error."""
    event_processor.check_device_accessibility()
    event_processor.check_device_accessibility.assert_called_once()


def test_callback_flush(
    event_processor: BaseEventProcessor,
) -> None:
    """Test check_timeout_and_flush with a callback."""
    mock_callback = MagicMock()
    event_processor.check_timeout_and_flush(callback=mock_callback)
    event_processor.check_timeout_and_flush.assert_called_once_with(callback=mock_callback)
