"""Tests for the CLI class."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from typetrace.backend.cli import CLI
from typetrace.config import Config, ExitCodes

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


@pytest.fixture
def cli() -> CLI:
    """Provide a CLI instance for testing."""
    return CLI()


@pytest.fixture
def mock_db_path(tmp_path: Path) -> Path:
    """Provide a mock database path."""
    return tmp_path / "test.db"


@pytest.fixture
def mock_db_manager(mocker: MockerFixture, cli: CLI) -> Mock:
    """Mock the DatabaseManager."""
    mock_manager = mocker.Mock()
    mocker.patch.object(cli, "_CLI__db_manager", mock_manager)
    return mock_manager


@pytest.fixture
def mock_logger(mocker: MockerFixture) -> Mock:
    """Mock the logger."""
    return mocker.patch("typetrace.backend.cli.logger")


@pytest.fixture
def mock_processor(mocker: MockerFixture) -> Mock:
    """Mock the event processor."""
    mock_proc = mocker.Mock()
    mock_proc.trace = mocker.Mock()
    mock_proc.stop = mocker.Mock()
    return mock_proc


@pytest.fixture
def mock_dbus_manager(mocker: MockerFixture) -> Mock:
    """Mock the DbusServiceManager."""
    mock_dbus = mocker.Mock()
    mock_dbus.run.return_value = 0
    mocker.patch("typetrace.backend.cli.DbusServiceManager", return_value=mock_dbus)
    return mock_dbus


@pytest.fixture
def mock_thread(mocker: MockerFixture) -> Mock:
    """Mock the threading.Thread."""
    mock_thread_instance = mocker.Mock()
    mocker.patch(
        "threading.Thread", return_value=mock_thread_instance,
    )
    return mock_thread_instance


@pytest.fixture
def mock_platform(mocker: MockerFixture, request: pytest.FixtureRequest) -> Mock:
    """Mock the platform.system function."""
    platform_name = getattr(request, "param", "Linux")
    mock_platform = mocker.patch("platform.system", return_value=platform_name)
    return mock_platform


@pytest.fixture
def mock_linux_processor(mocker: MockerFixture) -> Mock:
    """Mock the LinuxEventProcessor."""
    mock_processor = mocker.Mock()
    mocker.patch("typetrace.backend.events.linux.LinuxEventProcessor", return_value=mock_processor)
    return mock_processor


@pytest.fixture
def mock_windows_darwin_processor(mocker: MockerFixture) -> Mock:
    """Mock the WindowsDarwinEventProcessor."""
    mock_processor = mocker.Mock()
    mocker.patch(
        "typetrace.backend.events.windows_darwin.WindowsDarwinEventProcessor",
        return_value=mock_processor,
    )
    return mock_processor


# =============================================================================
# ========================= Tests for CLI.run method ==========================
# =============================================================================
@pytest.mark.parametrize("mock_platform", ["Linux"], indirect=True)
def test_run_linux(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_platform: Mock,
    mock_linux_processor: Mock,
    mock_thread: Mock,
    mock_dbus_manager: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method on Linux platform."""
    mocker.patch.object(Config, "IS_FLATPAK", False)
    mock_check_input = mocker.patch.object(cli, "_check_input_group")
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)
    mock_logger_setup = mocker.patch("typetrace.backend.cli.LoggerSetup")
    result = cli.run()

    assert result == ExitCodes.SUCCESS

    mock_logger_setup.setup_logging.assert_called_once()
    mock_db_manager.initialize_database.assert_called_once_with(mock_db_path)
    mock_check_input.assert_called_once()
    mock_linux_processor.check_device_accessibility.assert_called_once()

    assert mock_thread.start.call_count == 1

    mock_dbus_manager.run.assert_called_once()


@pytest.mark.parametrize("mock_platform", ["Unsupported"], indirect=True)
def test_run_unsupported_platform(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_platform: Mock,
    mock_logger: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method on an unsupported platform."""
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)
    result = cli.run()

    assert result == ExitCodes.PLATFORM_ERROR

    mock_logger.error.assert_called_once_with("Unsupported platform: %s", "Unsupported")


def test_run_database_error(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_logger: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method handles database errors."""
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)

    mock_db_manager.initialize_database.side_effect = sqlite3.Error("Test DB error")
    result = cli.run()

    assert result == ExitCodes.DATABASE_ERROR

    mock_logger.exception.assert_called_once()


def test_run_permission_error(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_logger: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method handles permission errors."""
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)
    mock_db_manager.initialize_database.side_effect = PermissionError("Test permission error")
    result = cli.run()

    assert result == ExitCodes.PERMISSION_ERROR

    mock_logger.exception.assert_called_once()


def test_run_runtime_error(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_logger: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method handles runtime errors."""
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)
    mock_db_manager.initialize_database.side_effect = RuntimeError("Test runtime error")
    result = cli.run()

    assert result == ExitCodes.RUNTIME_ERROR

    mock_logger.exception.assert_called_once()


def test_run_cleanup(
    cli: CLI,
    mock_db_path: Path,
    mock_db_manager: Mock,
    mock_platform: Mock,
    mock_linux_processor: Mock,
    mock_thread: Mock,
    mock_logger: Mock,
    mocker: MockerFixture,
) -> None:
    """Test the run method cleans up resources."""
    mocker.patch.object(cli, "_CLI__db_path", mock_db_path)
    mocker.patch.object(Config, "IS_FLATPAK", True)
    mocker.patch.object(cli, "_check_input_group")
    mock_thread.is_alive.return_value = True
    cli._processor_thread = mock_thread

    mock_dbus = mocker.Mock()
    mock_dbus.run.side_effect = RuntimeError("Test dbus error")
    mocker.patch("typetrace.backend.cli.DbusServiceManager", return_value=mock_dbus)
    result = cli.run()

    assert result == ExitCodes.RUNTIME_ERROR

    mock_linux_processor.stop.assert_called_once()
    mock_thread.join.assert_called_once()
    mock_logger.info.assert_any_call("TypeTrace Backend finished.")
