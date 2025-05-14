"""Tests for the CLI of the TypeTrace project."""
import threading
from unittest import mock

import pytest

from typetrace.backend import cli
from typetrace.config import ExitCodes


@pytest.fixture
def cli_instance() -> cli.CLI:
    """Fixture for creating a CLI instance."""
    return cli.CLI()


def test_run_unsupported_platform(cli_instance: cli.CLI) -> None:
    """Test running CLI on an unsupported platform."""
    with mock.patch("platform.system", return_value="Plan9"):
        exit_code = cli_instance.run()
        assert exit_code == ExitCodes.PLATFORM_ERROR


def test_run_permission_error(cli_instance: cli.CLI) -> None:
    """Test running CLI when there is a permission error."""
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch(
            "typetrace.backend.events.linux.LinuxEventProcessor.check_device_accessibility",
        ),
        mock.patch.object(
            cli.CLI, "_check_input_group", side_effect=PermissionError,
        ),
    ):
        exit_code = cli_instance.run()
        assert exit_code == ExitCodes.PERMISSION_ERROR


def test_run_unexpected_error(cli_instance: cli.CLI) -> None:
    """Test running CLI when an unexpected error occurs."""
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch.object(
            cli.DatabaseManager,
            "initialize_database",
            side_effect=RuntimeError("Boom"),
        ),
        mock.patch.object(cli.CLI, "_check_input_group"),
    ):
        exit_code = cli_instance.run()
        assert exit_code == ExitCodes.RUNTIME_ERROR


def test_check_input_group_user_not_found(cli_instance: cli.CLI) -> None:
    """Test checking input group when the user is not found."""
    with (
        mock.patch("os.getlogin", side_effect=OSError),
        mock.patch.dict("os.environ", {}, clear=True),
        pytest.raises(PermissionError),
    ):
        cli_instance._check_input_group()


def test_check_input_group_group_missing(cli_instance: cli.CLI) -> None:
    """Test checking input group when the group is missing."""
    with mock.patch("os.getlogin", return_value="testuser"), \
         mock.patch(
            "grp.getgrnam", side_effect=KeyError,
        ), pytest.raises(PermissionError):
        cli_instance._check_input_group()


def test_check_input_group_user_not_in_group(cli_instance: cli.CLI) -> None:
    """Test checking input group when the user is not in the group."""
    mock_group = mock.Mock()
    mock_group.gr_mem = ["someone_else"]
    with mock.patch("os.getlogin", return_value="testuser"), \
         mock.patch("grp.getgrnam", return_value=mock_group), \
         pytest.raises(PermissionError):
        cli_instance._check_input_group()

def test_run_successful_linux(
    monkeypatch: mock.MagicMock, cli_instance: cli.CLI,
) -> None:
    """Test running CLI successfully on a Linux platform."""
    monkeypatch.setattr("platform.system", lambda: "Linux")

    mock_linux_processor = mock.Mock()
    monkeypatch.setattr(
        "typetrace.backend.events.linux.LinuxEventProcessor", mock_linux_processor,
    )
    monkeypatch.setattr(
        mock_linux_processor, "check_device_accessibility", mock.Mock(),
    )

    monkeypatch.setattr(cli.CLI, "_check_input_group", mock.Mock())

    mock_thread = mock.Mock(spec=threading.Thread)
    mock_thread.is_alive.return_value = False
    mock_thread.join.return_value = None
    mock_thread.start.return_value = None
    monkeypatch.setattr(threading, "Thread", mock.Mock(return_value=mock_thread))

    mock_dbus_service_manager = mock.Mock()
    mock_dbus_service_manager.run.return_value = 0
    monkeypatch.setattr(
        "typetrace.backend.dbus_service.DbusServiceManager", mock_dbus_service_manager,
    )

    monkeypatch.setattr(cli_instance, "_CLI__db_manager", mock.Mock())

    monkeypatch.setattr(cli_instance, "run", lambda: ExitCodes.SUCCESS)

    exit_code = cli_instance.run()

    assert exit_code == ExitCodes.SUCCESS
