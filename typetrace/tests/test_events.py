import pytest  # noqa: F401
from pathlib import Path
import time
import evdev
from typetrace.backend.events import (
    process_single_event,
    read_device_events,
    check_timeout_and_flush,
    buffer_keys,
    trace_keys,
    print_key,
)
from typetrace.backend.config import BUFFER_TIMEOUT, KeyEvent


# Test for print_key function
def test_print_key(mocker):
    mock_logger = mocker.patch("typetrace.backend.events.logger.debug")
    event: KeyEvent = {"name": "KEY_A", "scan_code": 30}
    print_key(event)
    mock_logger.assert_called_once_with(
        '{"key_name": "%s", "key_code": %s}', "KEY_A", 30
    )


# Test for process_single_event (Keypress event)
def test_process_single_event_keypress(mocker):
    mock_event = mocker.Mock(type=evdev.ecodes.EV_KEY, value=1, code=evdev.ecodes.KEY_A)

    mock_db_path = Path("/mock/db/path")
    mocker.patch("typetrace.backend.events.write_to_database")
    buffer = []
    start_time = time.time()

    new_buffer, new_start_time = process_single_event(
        mock_event, buffer, start_time, mock_db_path
    )

    assert len(new_buffer) == 1
    assert new_buffer[0]["scan_code"] == evdev.ecodes.KEY_A
    assert new_buffer[0]["name"] == "KEY_A"
    assert new_start_time == start_time


# Test for read_device_events function
def test_read_device_events(mocker):
    mock_device = mocker.Mock(spec=evdev.device.InputDevice)
    mock_event = mocker.Mock(type=evdev.ecodes.EV_KEY, value=1, code=evdev.ecodes.KEY_B)
    mock_device.read.return_value = [mock_event]
    mock_db_path = Path("/mock/db/path")
    mock_process = mocker.patch("typetrace.backend.events.process_single_event")
    fixed_time = time.time() + 1
    mock_process.return_value = ([], fixed_time)
    buffer = []
    start_time = time.time()

    new_buffer, new_start_time = read_device_events(
        mock_device, buffer, start_time, mock_db_path
    )

    assert mock_device.read.called
    assert new_buffer == []
    assert new_start_time == fixed_time
    assert new_start_time > start_time


# Test for read_device_events when an OSError occurs
def test_read_device_events_oserror(mocker):
    mock_device = mocker.Mock(spec=evdev.device.InputDevice)
    mock_device.read.side_effect = OSError("Device error")
    mock_logger = mocker.patch("typetrace.backend.events.logger.exception")
    mock_db_path = Path("/mock/db/path")
    buffer = []
    start_time = time.time()

    new_buffer, new_start_time = read_device_events(
        mock_device, buffer, start_time, mock_db_path
    )

    assert new_buffer == buffer
    assert new_start_time == start_time
    mock_logger.assert_called_once_with("Error reading from device")


# Test for check_timeout_and_flush when timeout occurs
def test_check_timeout_and_flush_timeout(mocker):
    mock_db_path = Path("/mock/db/path")
    mock_write = mocker.patch("typetrace.backend.events.write_to_database")
    buffer = [{"scan_code": 1, "name": "KEY_1"}]
    start_time = time.time() - BUFFER_TIMEOUT - 1
    mock_time = mocker.patch("time.time")
    mock_time.return_value = start_time + BUFFER_TIMEOUT + 2

    new_buffer, new_start_time = check_timeout_and_flush(
        buffer, start_time, mock_db_path
    )

    assert len(new_buffer) == 0
    mock_write.assert_called_once_with(mock_db_path, buffer)
    assert new_start_time == start_time + BUFFER_TIMEOUT + 2


# Test for check_timeout_and_flush when timeout has not yet occurred
def test_check_timeout_and_flush_no_timeout(mocker):
    mock_db_path = Path("/mock/db/path")
    mock_write = mocker.patch("typetrace.backend.events.write_to_database")
    buffer = [{"scan_code": 1, "name": "KEY_1"}]
    start_time = time.time()
    mocker.patch("time.time", return_value=start_time + BUFFER_TIMEOUT - 1)

    new_buffer, new_start_time = check_timeout_and_flush(
        buffer, start_time, mock_db_path
    )

    assert new_buffer == buffer
    assert new_start_time == start_time
    mock_write.assert_not_called()


# Test for buffer_keys function
def test_buffer_keys(mocker):
    mock_device = mocker.Mock(spec=evdev.device.InputDevice)
    mock_select = mocker.patch("select.select")
    mock_select.side_effect = [
        ([mock_device], [], []),
        KeyboardInterrupt,
    ]
    mocker.patch(
        "typetrace.backend.events.read_device_events",
        return_value=([], time.time()),
    )
    mocker.patch(
        "typetrace.backend.events.check_timeout_and_flush",
        return_value=([], time.time()),
    )
    mock_db_path = Path("/mock/db/path")
    mocker.patch(
        "typetrace.backend.events.select_keyboards",
        return_value=[mock_device],
    )

    buffer_keys([mock_device], mock_db_path)


# Test for trace_keys function
def test_trace_keys(mocker):
    mock_db_path = Path("/mock/db/path")
    mock_managed_devices = mocker.patch("typetrace.backend.devices.managed_devices")
    mock_device = mocker.Mock(spec=evdev.device.InputDevice)
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = [mock_device]
    mock_context.__exit__.return_value = None
    mock_managed_devices.return_value = mock_context
    mock_buffer_keys = mocker.patch("typetrace.backend.events.buffer_keys")

    trace_keys(mock_db_path)

    mock_buffer_keys.assert_called_once_with([mock_device], mock_db_path)
