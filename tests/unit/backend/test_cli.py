"""Tests for the CLI class."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from typetrace.backend.cli import CLI, _run_processor_thread
from typetrace.backend.events.linux import LinuxEventProcessor
from typetrace.config import ExitCodes

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


# =============================================================================
# ========================== Fixtures =========================================
# =============================================================================
@pytest.fixture
def cli_instance() -> CLI:
    """Provide a CLI instance for testing."""
    return CLI()


@pytest.fixture
def mock_db_path(mocker: MockerFixture) -> Path:
    """Mock the database path."""
    mock_path = mocker.patch("typetrace.config.DatabasePath")
    mock_path.DB_PATH = mocker.Mock(spec=Path)
    return mock_path.DB_PATH


@pytest.fixture
def mock_processor(mocker: MockerFixture) -> LinuxEventProcessor:
    """Mock the LinuxEventProcessor."""
    processor = mocker.Mock(spec=LinuxEventProcessor)
    processor.trace = mocker.Mock()
    processor.stop = mocker.Mock()
    processor.check_device_accessibility = mocker.Mock()
    return processor


# =============================================================================
# =================== Tests for _run_processor_thread =========================
# =============================================================================
def test_run_processor_thread_handles_exception(
    mock_processor: LinuxEventProcessor,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _run_processor_thread logs exceptions."""
    caplog.set_level(logging.DEBUG)
    mock_processor.trace.side_effect = RuntimeError("Processor error")

    _run_processor_thread(mock_processor)

    assert "Unhandled exception in event processor thread" in caplog.text
    assert "Processor error" in caplog.text
    assert "Event processor thread started" in caplog.text
    assert "Event processor thread finished" in caplog.text


# =============================================================================
# =================== Tests for platform detection ============================
# =============================================================================
# FIXME
def test_run_linux_platform(
    cli_instance: CLI,
    mocker: MockerFixture,
    mock_db_path: Path,
    mock_processor: Mock,
) -> None:
    """Test run method on Linux platform."""
    mocker.patch("platform.system", return_value="Linux")
    mocker.patch(
        "typetrace.backend.events.linux.LinuxEventProcessor",
        return_value=mock_processor,
    )
    mocker.patch("typetrace.config.Config.IS_FLATPAK", False)
    mocker.patch.object(cli_instance, "_check_input_group")
    mock_db_init = mocker.patch(
        "typetrace.backend.db.DatabaseManager.initialize_database",
    )

    # Ensure the mock_db_path is used by CLI
    mocker.patch("typetrace.config.DatabasePath.DB_PATH", mock_db_path)

    exit_code = cli_instance.run()

    assert exit_code == ExitCodes.SUCCESS
    mock_db_init.assert_called_once_with(mock_db_path)
    mock_processor.check_device_accessibility.assert_called_once()
    assert cli_instance._processor_thread is not None


# FIXME
def test_run_unknown_platform(
    cli_instance: CLI,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test run method on unsupported platform."""
    caplog.set_level(logging.INFO, logger="typetrace.backend.cli")
    mocker.patch("platform.system", return_value="TestOS")

    exit_code = cli_instance.run()

    assert "Unsupported platform: TestOS" in caplog.text
    assert exit_code == ExitCodes.PLATFORM_ERROR


# =============================================================================
# =================== Tests for try-except block ==============================
# =============================================================================
@pytest.mark.parametrize(
    ("exception_type", "exit_code", "log_message"),
    [
        (
            PermissionError,
            ExitCodes.PERMISSION_ERROR,
            "Please ensure you have sufficient permissions",
        ),
        (sqlite3.Error, ExitCodes.DATABASE_ERROR, "Database error"),
        (OSError, ExitCodes.RUNTIME_ERROR, "Unexpected error"),
        (ValueError, ExitCodes.RUNTIME_ERROR, "Unexpected error"),
        (RuntimeError, ExitCodes.RUNTIME_ERROR, "Unexpected error"),
    ],
)
# FIXME
def test_run_catches_exceptions(
    cli_instance: CLI,
    mocker: MockerFixture,
    exception_type: type[Exception],
    exit_code: ExitCodes,
    log_message: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test run method handles various exceptions."""
    caplog.set_level(logging.INFO)
    mocker.patch("platform.system", return_value="Linux")
    mocker.patch(
        "typetrace.backend.db.DatabaseManager.initialize_database",
        side_effect=exception_type("Test error"),
    )

    result = cli_instance.run()

    assert result == exit_code
    assert log_message in caplog.text
    assert "Test error" in caplog.text


# FIXME
def test_run_finally_block(
    cli_instance: CLI,
    mocker: MockerFixture,
    mock_processor: LinuxEventProcessor,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test run method executes finally block for shutdown."""
    caplog.set_level(logging.DEBUG)
    mocker.patch("platform.system", return_value="Linux")
    mocker.patch(
        "typetrace.backend.cli.LinuxEventProcessor",
        return_value=mock_processor,
    )
    mocker.patch("typetrace.config.Config.IS_FLATPAK", False)
    mocker.patch.object(cli_instance, "_check_input_group")
    mocker.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    # Mock thread to simulate being alive
    mock_thread = mocker.Mock()
    mock_thread.is_alive.return_value = True
    mocker.patch("threading.Thread", return_value=mock_thread)

    cli_instance.run()

    assert "Initiating backend shutdown sequence" in caplog.text
    assert "Processor thread will be terminated" in caplog.text
    mock_processor.stop.assert_called_once()
    mock_thread.join.assert_called_once()


# =============================================================================
# =================== Tests for _check_input_group ============================
# =============================================================================
def test_check_input_group_user_in_group(
    cli_instance: CLI,
    mocker: MockerFixture,
) -> None:
    """Test _check_input_group when user is in input group."""
    mocker.patch("os.getlogin", return_value="testuser")
    mock_group = mocker.Mock()
    mock_group.gr_mem = ["testuser"]
    mocker.patch("grp.getgrnam", return_value=mock_group)

    cli_instance._check_input_group()


def test_check_input_group_not_in_group(
    cli_instance: CLI,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_input_group when user is not in input group."""
    caplog.set_level(logging.INFO)
    mocker.patch("os.getlogin", return_value="testuser")
    mock_group = mocker.Mock()
    mock_group.gr_mem = ["otheruser"]
    mocker.patch("grp.getgrnam", return_value=mock_group)

    with pytest.raises(PermissionError):
        cli_instance._check_input_group()

    assert "The User testuser is not in the 'input' group" in caplog.text


def test_check_input_group_does_not_exist(
    cli_instance: CLI,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_input_group when input group does not exist."""
    caplog.set_level(logging.INFO)
    mocker.patch("os.getlogin", return_value="testuser")
    mocker.patch("grp.getgrnam", side_effect=KeyError("input"))

    with pytest.raises(PermissionError):
        cli_instance._check_input_group()

    assert "The 'input' group does not exist" in caplog.text


def test_check_input_group_username_oserror(
    cli_instance: CLI,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _check_input_group when username cannot be determined."""
    caplog.set_level(logging.INFO)
    mocker.patch("os.getlogin", side_effect=OSError("No login"))
    mocker.patch("os.getenv", return_value=None)

    with pytest.raises(PermissionError):
        cli_instance._check_input_group()

    assert "Could not determine username" in caplog.text
