"""Tests for the LinuxEventProcessor class."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from typetrace.backend.events.linux import LinuxEventProcessor
from typetrace.config import Config, Event

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


@pytest.fixture
def event_processor(
    tmp_path: Path,
) -> LinuxEventProcessor:
    """Provide a LinuxEventProcessor instance for testing."""
    return LinuxEventProcessor(tmp_path / "test.db")


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    """Provide a mock database path."""
    return tmp_path / "test.db"


@pytest.fixture
def mock_db_manager(
    mocker: MockerFixture,
    event_processor: LinuxEventProcessor,
) -> Mock:
    """Mock the DB manager."""
    return mocker.patch.object(
        event_processor,
        "_BaseEventProcessor__db_manager",
    )


@pytest.fixture
def mock_time(mocker: MockerFixture) -> Mock:
    """Mock time.time function."""
    return mocker.patch("time.time")


@pytest.fixture
def mock_datetime(mocker: MockerFixture) -> tuple[Mock, Mock]:
    """Mock datetime for consistent date values."""
    mock_now = mocker.patch("datetime.datetime")
    mock_dt = mocker.Mock()
    mock_now.now.return_value = mock_dt
    mock_dt.strftime.return_value = "2022-01-02"
    return mock_now, mock_dt


@pytest.fixture
def mock_evdev(mocker: MockerFixture) -> Mock:
    """Mock evdev module."""
    mock_ev = mocker.patch("typetrace.backend.events.linux.evdev")
    mock_ev.ecodes.EV_KEY = 1
    mock_ev.ecodes.KEY = {30: "KEY_A", 42: "KEY_LEFTSHIFT"}
    return mock_ev


# =============================================================================
# ==================== Tests for _check_timeout_and_flush method ==============
# =============================================================================
def test_check_timeout_and_flush_empty_buffer(
    event_processor: LinuxEventProcessor,
    mock_db_path: Path,
    mock_db_manager: Mock,
) -> None:
    """Test check_timeout_and_flush with an empty buffer."""
    buffer: list[Event] = []
    start_time = 100.0

    new_buffer, new_start_time = event_processor._check_timeout_and_flush(
        buffer,
        start_time,
        mock_db_path,
    )

    assert new_buffer == []
    assert new_start_time == start_time
    mock_db_manager.write_to_database.assert_not_called()


def test_check_timeout_and_flush_timeout_reached(
    event_processor: LinuxEventProcessor,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_time: Mock,
) -> None:
    """Test check_timeout_and_flush when timeout is reached."""
    start_time = 100.0
    mock_time.return_value = start_time + Config.BUFFER_TIMEOUT + 1

    buffer: list[Event] = [{"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"}]

    new_buffer, new_start_time = event_processor._check_timeout_and_flush(
        buffer,
        start_time,
        mock_db_path,
    )

    assert new_buffer == []
    assert new_start_time == mock_time.return_value
    mock_db_manager.write_to_database.assert_called_once_with(mock_db_path, buffer)


def test_check_timeout_and_flush_buffer_size_reached(
    event_processor: LinuxEventProcessor,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_time: Mock,
) -> None:
    """Test check_timeout_and_flush when buffer size limit is reached."""
    start_time = 100.0
    current_time = 101.0
    mock_time.return_value = current_time

    buffer: list[Event] = [
        {"scan_code": i, "name": f"KEY_{i}", "date": "2022-01-01"}
        for i in range(Config.BUFFER_SIZE)
    ]

    new_buffer, new_start_time = event_processor._check_timeout_and_flush(
        buffer,
        start_time,
        mock_db_path,
    )

    assert new_buffer == []
    assert new_start_time == current_time
    mock_db_manager.write_to_database.assert_called_once_with(mock_db_path, buffer)


def test_check_timeout_and_flush_force_flush(
    event_processor: LinuxEventProcessor,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_time: Mock,
) -> None:
    """Test check_timeout_and_flush with force flush parameter."""
    start_time = 100.0
    current_time = start_time + 1.0
    mock_time.return_value = current_time

    buffer: list[Event] = [{"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"}]

    new_buffer, new_start_time = event_processor._check_timeout_and_flush(
        buffer,
        start_time,
        mock_db_path,
        flush=True,
    )

    assert new_buffer == []
    assert new_start_time == current_time
    mock_db_manager.write_to_database.assert_called_once_with(mock_db_path, buffer)


def test_check_timeout_and_flush_with_callback(
    mock_db_path: Path,
    mock_time: Mock,
    mocker: MockerFixture,
) -> None:
    """Test check_timeout_and_flush calls callback when database is updated."""
    mock_callback = mocker.Mock()
    event_processor = LinuxEventProcessor(mock_db_path, mock_callback)
    mock_db_manager = mocker.patch.object(
        event_processor,
        "_BaseEventProcessor__db_manager",
    )

    start_time = 100.0
    mock_time.return_value = start_time + Config.BUFFER_TIMEOUT + 1

    buffer: list[Event] = [{"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"}]

    event_processor._check_timeout_and_flush(buffer, start_time, mock_db_path)
    mock_db_manager.write_to_database.assert_called_once()
    mock_callback.assert_called_once()


# =============================================================================
# ==================== Tests for _process_single_event method =================
# =============================================================================
def test_process_single_event_key_press(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test processing a key press event."""
    # Create a key press event
    mock_event = mocker.Mock()
    mock_event.type = 1  # EV_KEY
    mock_event.value = 1  # KEY_PRESS
    mock_event.code = 30  # KEY_A

    test_date = "2022-01-01"
    event_processor._current_date = test_date
    mock_print_event = mocker.patch.object(event_processor, "_print_event")
    result = event_processor._process_single_event(mock_event)

    expected_event = {
        "scan_code": 30,
        "name": "KEY_A",
        "date": test_date,
    }

    assert result == expected_event
    mock_print_event.assert_called_once_with(expected_event)


def test_process_single_event_key_release(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test processing a key release event - should be ignored."""
    # Create a key release event
    mock_event = mocker.Mock()
    mock_event.type = 1  # EV_KEY
    mock_event.value = 0  # KEY_RELEASE
    mock_event.code = 30  # KEY_A

    mock_print_event = mocker.patch.object(event_processor, "_print_event")
    result = event_processor._process_single_event(mock_event)

    assert result is None
    mock_print_event.assert_not_called()


def test_process_single_event_non_key_event(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test processing a non-key event."""
    # Create a non-key event
    mock_event = mocker.Mock()
    mock_event.type = 2  # Not EV_KEY
    mock_event.value = 1  # KEY_PRESS
    mock_event.code = 30  # KEY_A

    mock_print_event = mocker.patch.object(event_processor, "_print_event")
    result = event_processor._process_single_event(mock_event)

    assert result is None
    mock_print_event.assert_not_called()


# =============================================================================
# ====================== Tests for trace and _buffer methods ==================
# =============================================================================
def test_trace_no_devices(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test trace method when no devices are found."""
    mock_managed_devices = mocker.patch.object(event_processor, "_managed_devices")

    # Context manager yields empty list (no devices)
    mock_managed_devices.return_value.__enter__.return_value = []
    mock_buffer = mocker.patch.object(event_processor, "_buffer")

    event_processor.trace()
    mock_buffer.assert_not_called()


def test_trace_with_devices(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test trace method with devices."""
    mock_devices = [mocker.Mock(), mocker.Mock()]
    mock_managed_devices = mocker.patch.object(event_processor, "_managed_devices")
    mock_managed_devices.return_value.__enter__.return_value = mock_devices
    mock_buffer = mocker.patch.object(event_processor, "_buffer")

    event_processor.trace()
    mock_buffer.assert_called_once_with(mock_devices)


def test_read_device_events_success(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test _read_device_events successfully reads events."""
    mock_device = mocker.Mock()
    mock_event = mocker.Mock()

    mock_device.read.return_value = [mock_event]

    mock_process = mocker.patch.object(event_processor, "_process_single_event")
    key_event = {"scan_code": 30, "name": "KEY_A", "date": "2022-01-01"}
    mock_process.return_value = key_event

    buffer: list[Event] = []

    result = event_processor._read_device_events(mock_device, buffer)

    mock_device.read.assert_called_once()
    mock_process.assert_called_once_with(mock_event)

    assert result == [key_event]


def test_read_device_events_error(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test _read_device_events handles errors."""
    mock_device = mocker.Mock()

    mock_device.read.side_effect = OSError("Device error")

    buffer: list[Event] = [
        {"scan_code": 42, "name": "KEY_LEFTSHIFT", "date": "2022-01-01"}
    ]

    result = event_processor._read_device_events(mock_device, buffer)
    assert result == buffer


def test_check_device_accessibility_no_devices(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test check_device_accessibility when no devices are found."""
    mock_select = mocker.patch.object(event_processor, "_select_devices")
    mock_select.return_value = []

    event_processor.check_device_accessibility()
    mock_select.assert_called_once()


def test_check_device_accessibility_permission_error(
    event_processor: LinuxEventProcessor,
    mocker: MockerFixture,
) -> None:
    """Test check_device_accessibility with permission error."""
    mock_select = mocker.patch.object(event_processor, "_select_devices")
    mock_select.side_effect = PermissionError("Permission denied")

    event_processor.check_device_accessibility()

    mock_select.assert_called_once()
