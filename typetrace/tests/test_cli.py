# Please check your path if the following path does not work:
# "~/.local/share/typetrace"
import pytest
from pathlib import Path
from typetrace.backend.cli import (
    resolve_db_path,
    check_input_group,
    main,
    ExitCodes,
)


# Test for resolve_db_path (with mocked path)
def test_resolve_db_path(mocker):
    # Mock user_data_dir to return a predefined directory
    mock_user_data_dir = mocker.patch(
        "appdirs.user_data_dir", return_value="/mock/data/dir"
    )
    # Mock mkdir to prevent actual directory creation
    mock_mkdir = mocker.patch("pathlib.Path.mkdir")

    # Call the function and verify the expected database path
    db_path = resolve_db_path()
    assert db_path == Path("/mock/data/dir/TypeTrace.db")

    # Ensure mocks were called correctly
    mock_user_data_dir.assert_called_once_with("typetrace")
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


# Test for check_input_group (user not in the required group)
def test_check_input_group_user_not_in_group(mocker):
    # Mock user login and group lookup
    mocker.patch("os.getlogin", return_value="testuser")
    mocker.patch("grp.getgrnam", return_value=mocker.Mock(gr_mem=[]))

    # Expect a PermissionError if the user is not in the group
    with pytest.raises(PermissionError):
        check_input_group()


# Test for main (successful execution)
def test_main_success(mocker):
    # Mock arguments
    mock_args = mocker.Mock(debug=False)

    # Mock dependencies to prevent real execution
    mocker.patch("typetrace.backend.cli.check_input_group")
    mocker.patch("typetrace.backend.devices.check_device_accessibility")
    mocker.patch("typetrace.backend.db.initialize_database")
    # Should now work
    mocker.patch("typetrace.backend.events.trace_keys")

    # Execute the main function and check the exit code
    exit_code = main(mock_args)
    assert exit_code == ExitCodes.SUCCESS


# Test for main (PermissionError scenario)
def test_main_permission_error(mocker):
    # Mock arguments
    mock_args = mocker.Mock(debug=False)

    # Simulate a PermissionError during check_input_group
    mocker.patch(
        "typetrace.backend.cli.check_input_group",
        side_effect=PermissionError,
    )

    # Execute main and verify the exit code for permission error
    exit_code = main(mock_args)
    assert exit_code == ExitCodes.PERMISSION_ERROR


# Optional test for resolve_db_path with an actual path
def test_resolve_db_path_real_path(mocker):
    # Mock user_data_dir to return the real user data directory
    mock_user_data_dir = mocker.patch(
        "appdirs.user_data_dir", return_value="~/.local/share/typetrace"
    )
    # Mock mkdir to prevent actual directory creation
    mock_mkdir = mocker.patch("pathlib.Path.mkdir")

    # Call the function and verify the expected database path
    db_path = resolve_db_path()
    assert db_path == Path("~/.local/share/typetrace/TypeTrace.db")

    # Ensure mocks were called correctly
    mock_user_data_dir.assert_called_once_with("typetrace")
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
