import argparse
import sqlite3
from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

# Modules to test/mock
from typetrace.backend.cli import CLI
from typetrace.config import Config, ExitCodes

# Define mock paths/data upfront for consistency
MOCK_DB_PATH = Path("/fake/test/path/typetrace.db")
MOCK_USERNAME = "testuser"

# --- Fixtures ---


@pytest.fixture
def mock_args(debug=False):
    """Creates mock argparse.Namespace."""
    return argparse.Namespace(debug=debug)


@pytest.fixture
def cli_instance():
    """Provides a CLI instance with a mocked DB path."""
    with patch("backend.cli.DatabasePath.DB_PATH", MOCK_DB_PATH):
        yield CLI()


@pytest.fixture(autouse=True)
def reset_config_debug():
    """Ensures Config.DEBUG is reset after each test."""
    original_debug = Config.DEBUG
    yield
    Config.DEBUG = original_debug


@pytest.fixture
def mock_dependencies():
    """Central fixture to patch multiple dependencies."""
    # Use autospec=True where possible for better mock signatures
    with (
        patch(
            "backend.cli.DatabaseManager.initialize_database", autospec=True
        ) as mock_init_db,
        patch(
            "backend.cli.LoggerSetup.setup_logging", autospec=True
        ) as mock_setup_logging,
        patch("platform.system") as mock_platform_system,
        patch("backend.cli.logging.getLogger") as mock_get_logger,
        patch("backend.events.linux.LinuxEventProcessor") as MockLinuxProcessor,
        patch(
            "backend.events.windows_darwin.WindowsDarwinEventProcessor"
        ) as MockWinDarProcessor,
        patch("backend.cli.CLI._check_input_group") as mock_check_input_group,
        patch("backend.cli.Config") as MockConfig,
    ):  # Patch Config to control IS_FLATPAK
        # Configure the mock logger
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        # Configure mock Config attributes used in CLI
        MockConfig.IS_FLATPAK = False  # Default to non-flatpak for tests
        MockConfig.DEBUG = Config.DEBUG  # Reflect actual Config state initially

        yield {
            "init_db": mock_init_db,
            "setup_logging": mock_setup_logging,
            "platform_system": mock_platform_system,
            "get_logger": mock_get_logger,
            "logger_instance": mock_logger_instance,
            "LinuxProcessor": MockLinuxProcessor,
            "WinDarProcessor": MockWinDarProcessor,
            "check_input_group": mock_check_input_group,
            "MockConfig": MockConfig,
        }


# --- Test Cases ---


def test_cli_run_debug_mode(cli_instance, mock_args, mock_dependencies):
    """Test if debug mode sets Config.DEBUG and calls logging setup."""
    args = mock_args(debug=True)
    mock_dependencies[
        "platform_system"
    ].return_value = "Linux"  # Assume Linux for this test

    cli_instance.run(args)

    assert Config.DEBUG is True
    mock_dependencies["setup_logging"].assert_called_once()
    # Check that initialization and processor setup still happen
    mock_dependencies["init_db"].assert_called_once_with(MOCK_DB_PATH)
    mock_dependencies["LinuxProcessor"].assert_called_once_with(MOCK_DB_PATH)


@pytest.mark.parametrize("system_name", ["Linux", "linux"])
def test_cli_run_linux_non_flatpak(
    cli_instance, mock_args, mock_dependencies, system_name
):
    """Test successful run on Linux (non-Flatpak)."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = system_name
    mock_dependencies["MockConfig"].IS_FLATPAK = False  # Explicitly set for clarity
    mock_processor_instance = mock_dependencies["LinuxProcessor"].return_value

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.SUCCESS
    mock_dependencies["init_db"].assert_called_once_with(MOCK_DB_PATH)
    mock_dependencies["check_input_group"].assert_called_once()
    mock_dependencies["LinuxProcessor"].assert_called_once_with(MOCK_DB_PATH)
    mock_processor_instance.check_device_accessibility.assert_called_once()
    mock_processor_instance.trace.assert_called_once()
    mock_dependencies[
        "WinDarProcessor"
    ].assert_not_called()  # Ensure other processor wasn't used


def test_cli_run_linux_flatpak(cli_instance, mock_args, mock_dependencies):
    """Test successful run on Linux (Flatpak)."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = "Linux"
    mock_dependencies["MockConfig"].IS_FLATPAK = True  # Set IS_FLATPAK
    mock_processor_instance = mock_dependencies["LinuxProcessor"].return_value

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.SUCCESS
    mock_dependencies["init_db"].assert_called_once_with(MOCK_DB_PATH)
    mock_dependencies[
        "check_input_group"
    ].assert_not_called()  # Should NOT be called in Flatpak
    mock_dependencies["LinuxProcessor"].assert_called_once_with(MOCK_DB_PATH)
    mock_processor_instance.check_device_accessibility.assert_called_once()
    mock_processor_instance.trace.assert_called_once()


@pytest.mark.parametrize("system_name", ["Darwin", "darwin", "Windows", "windows"])
def test_cli_run_windows_darwin(
    cli_instance, mock_args, mock_dependencies, system_name
):
    """Test successful run on Windows/Darwin."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = system_name
    mock_processor_instance = mock_dependencies["WinDarProcessor"].return_value

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.SUCCESS
    mock_dependencies["init_db"].assert_called_once_with(MOCK_DB_PATH)
    mock_dependencies["check_input_group"].assert_not_called()
    mock_dependencies["WinDarProcessor"].assert_called_once_with(MOCK_DB_PATH)
    mock_processor_instance.trace.assert_called_once()
    mock_dependencies["LinuxProcessor"].assert_not_called()


def test_cli_run_unsupported_platform(cli_instance, mock_args, mock_dependencies):
    """Test run on an unsupported platform."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = "SunOS"

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.PLATFORM_ERROR
    mock_dependencies["init_db"].assert_called_once_with(
        MOCK_DB_PATH
    )  # DB init happens before check
    mock_dependencies["logger_instance"].error.assert_called_once_with(
        "Unsupported platform: %s", "SunOS"
    )
    mock_dependencies["LinuxProcessor"].assert_not_called()
    mock_dependencies["WinDarProcessor"].assert_not_called()


def test_cli_run_permission_error_from_check(
    cli_instance, mock_args, mock_dependencies
):
    """Test handling PermissionError from _check_input_group."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = "Linux"
    mock_dependencies["MockConfig"].IS_FLATPAK = False
    mock_dependencies["check_input_group"].side_effect = PermissionError(
        "No input group access"
    )

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.PERMISSION_ERROR
    mock_dependencies["init_db"].assert_called_once()
    mock_dependencies["check_input_group"].assert_called_once()
    mock_dependencies["logger_instance"].exception.assert_called_once_with(
        ANY
    )  # Check exception was logged
    mock_dependencies[
        "LinuxProcessor"
    ].assert_not_called()  # Processor shouldn't be created


def test_cli_run_permission_error_from_processor(
    cli_instance, mock_args, mock_dependencies
):
    """Test handling PermissionError from processor."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = "Linux"
    mock_dependencies["MockConfig"].IS_FLATPAK = False
    mock_processor_instance = mock_dependencies["LinuxProcessor"].return_value
    mock_processor_instance.check_device_accessibility.side_effect = PermissionError(
        "Device access denied"
    )

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.PERMISSION_ERROR
    mock_dependencies["init_db"].assert_called_once()
    mock_dependencies["check_input_group"].assert_called_once()
    mock_dependencies["LinuxProcessor"].assert_called_once()
    mock_processor_instance.check_device_accessibility.assert_called_once()  # It was called
    mock_processor_instance.trace.assert_not_called()  # trace shouldn't be called
    mock_dependencies["logger_instance"].exception.assert_called_once_with(ANY)


def test_cli_run_database_error(cli_instance, mock_args, mock_dependencies):
    """Test handling sqlite3.Error."""
    args = mock_args()
    mock_dependencies["platform_system"].return_value = "Linux"
    mock_dependencies["init_db"].side_effect = sqlite3.Error(
        "Disk full"
    )  # Error during init

    exit_code = cli_instance.run(args)

    assert exit_code == ExitCodes.DATABASE_ERROR
    mock_dependencies["init_db"].assert_called_once()
    mock_dependencies["logger_instance"].exception.assert_called_once_with(
        "Database error"
    )
    mock_dependencies[
        "check_input_group"
    ].assert_not_called()  # Fails before platform check


# --- Tests for _check_input_group ---


@patch("backend.cli.os.getlogin", return_value=MOCK_USERNAME)
@patch("backend.cli.grp.getgrnam")
def test_check_input_group_user_in_group(
    mock_getgrnam, mock_getlogin, cli_instance, mock_dependencies
):
    """Test _check_input_group when user is in the 'input' group."""
    mock_group = MagicMock()
    mock_group.gr_mem = [MOCK_USERNAME, "otheruser"]
    mock_getgrnam.return_value = mock_group

    # No exception should be raised
    try:
        cli_instance._check_input_group()
    except PermissionError:
        pytest.fail("PermissionError raised unexpectedly")

    mock_getlogin.assert_called_once()
    mock_getgrnam.assert_called_once_with("input")
    mock_dependencies["logger_instance"].error.assert_not_called()


@patch("backend.cli.os.getlogin", return_value=MOCK_USERNAME)
@patch("backend.cli.grp.getgrnam")
def test_check_input_group_user_not_in_group(
    mock_getgrnam, mock_getlogin, cli_instance, mock_dependencies
):
    """Test _check_input_group when user is NOT in the 'input' group."""
    mock_group = MagicMock()
    mock_group.gr_mem = ["otheruser", "anotheruser"]
    mock_getgrnam.return_value = mock_group

    with pytest.raises(PermissionError):
        cli_instance._check_input_group()

    mock_getlogin.assert_called_once()
    mock_getgrnam.assert_called_once_with("input")
    mock_dependencies["logger_instance"].error.assert_called_once_with(
        "The User %s is not in the 'input' group", MOCK_USERNAME
    )
