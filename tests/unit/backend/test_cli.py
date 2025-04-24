"""Tests for the backend CLI module."""

import sqlite3
from unittest import mock

import pytest

from typetrace.backend.cli import CLI
from typetrace.config import ExitCodes


class TestCLI:
    """Test suite for the CLI class."""

    @pytest.fixture()
    def cli_instance(self) -> CLI:
        """Provide a CLI instance for testing.

        Returns
        -------
            A fresh CLI instance.

        """
        return CLI()

    # ==========================================
    # ========== Tests for run method ==========
    # ==========================================
    @mock.patch("platform.system")
    def test_run_unsupported_platform(
        self,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test run method with an unsupported platform.

        Args:
        ----
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "otherOS"
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.PLATFORM_ERROR

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.cli.CLI._check_input_group")
    def test_run_permission_error(
        self,
        mock_check_input: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test run method with a permission error.

        Args:
        ----
            mock_check_input: Mock for CLI._check_input_group.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        mock_check_input.side_effect = PermissionError("Permission denied")
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.PERMISSION_ERROR

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    def test_run_database_error(
        self,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test run method with a database error.

        Args:
        ----
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        mock_init_db.side_effect = sqlite3.Error("Database error")
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.DATABASE_ERROR

    @mock.patch("platform.system")
    @mock.patch(
        "typetrace.backend.db.DatabaseManager.initialize_database",
        side_effect=sqlite3.Error("DB error"),
    )
    @mock.patch(
        "typetrace.backend.cli.CLI._check_input_group",
        side_effect=PermissionError("Permission error"),
    )
    def test_run_multiple_errors_db_first(
        self,
        mock_check_input: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test that database errors take precedence over permission errors.

        Args:
        ----
            mock_check_input: Mock for CLI._check_input_group.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        args = mock.MagicMock()
        args.debug = False

        # The database error should be caught first since it happens earlier
        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.DATABASE_ERROR

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.cli.CLI._check_input_group")
    @mock.patch("typetrace.backend.events.linux.LinuxEventProcessor")
    def test_run_runtime_error(
        self,
        mock_event_processor: mock.MagicMock,
        mock_check_input: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test run method with a runtime error.

        Args:
        ----
            mock_event_processor: Mock for LinuxEventProcessor.
            mock_check_input: Mock for CLI._check_input_group.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        processor_instance = mock_event_processor.return_value
        processor_instance.trace.side_effect = RuntimeError("Runtime error")
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.RUNTIME_ERROR

    @mock.patch("platform.system")
    def test_run_platform_system_error(
        self,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test handling of platform.system() raising an exception.

        Args:
        ----
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.side_effect = OSError("platform.system error")
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)
        assert exit_code == ExitCodes.RUNTIME_ERROR

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.cli.CLI._check_input_group")
    @mock.patch("typetrace.backend.events.linux.LinuxEventProcessor")
    def test_run_linux_success(
        self,
        mock_event_processor: mock.MagicMock,
        mock_check_input: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test successful run method on Linux platform.

        Args:
        ----
            mock_event_processor: Mock for LinuxEventProcessor.
            mock_check_input: Mock for CLI._check_input_group.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        processor_instance = mock_event_processor.return_value
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)

        mock_init_db.assert_called_once()
        mock_event_processor.assert_called_once()
        processor_instance.trace.assert_called_once()

        assert exit_code == ExitCodes.SUCCESS

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.events.windows_darwin.WindowsDarwinEventProcessor")
    def test_run_windows_success(
        self,
        mock_event_processor: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test successful run method on Windows platform.

        Args:
        ----
            mock_event_processor: Mock for WindowsDarwinEventProcessor.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Windows"
        processor_instance = mock_event_processor.return_value
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)

        mock_init_db.assert_called_once()
        mock_event_processor.assert_called_once()
        processor_instance.trace.assert_called_once()

        assert exit_code == ExitCodes.SUCCESS

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.events.windows_darwin.WindowsDarwinEventProcessor")
    def test_run_darwin_success(
        self,
        mock_event_processor: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test successful run method on Darwin (macOS) platform.

        Args:
        ----
            mock_event_processor: Mock for WindowsDarwinEventProcessor.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Darwin"
        processor_instance = mock_event_processor.return_value
        args = mock.MagicMock()
        args.debug = False

        exit_code = cli_instance.run(args)

        mock_init_db.assert_called_once()
        mock_event_processor.assert_called_once()
        processor_instance.trace.assert_called_once()

        assert exit_code == ExitCodes.SUCCESS

    @mock.patch("platform.system")
    @mock.patch("typetrace.backend.db.DatabaseManager.initialize_database")
    @mock.patch("typetrace.backend.cli.CLI._check_input_group")
    @mock.patch("typetrace.backend.events.linux.LinuxEventProcessor")
    @mock.patch("typetrace.backend.logging_setup.LoggerSetup.setup_logging")
    def test_run_with_debug_flag(
        self,
        mock_setup_logging: mock.MagicMock,
        mock_event_processor: mock.MagicMock,
        mock_check_input: mock.MagicMock,
        mock_init_db: mock.MagicMock,
        mock_system: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test run method with debug flag set.

        Args:
        ----
            mock_setup_logging: Mock for LoggerSetup.setup_logging.
            mock_event_processor: Mock for LinuxEventProcessor.
            mock_check_input: Mock for CLI._check_input_group.
            mock_init_db: Mock for DatabaseManager.initialize_database.
            mock_system: Mock for platform.system function.
            cli_instance: CLI instance fixture.

        """
        mock_system.return_value = "Linux"
        args = mock.MagicMock()
        args.debug = True

        exit_code = cli_instance.run(args)

        mock_setup_logging.assert_called_once()

        assert exit_code == ExitCodes.SUCCESS

    # =========================================================
    # ========== Tests for _check_input_group method ==========
    # =========================================================
    @mock.patch("os.getlogin")
    @mock.patch("grp.getgrnam")
    def test_check_input_group_user_in_group(
        self,
        mock_getgrnam: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group when user is in the input group.

        Args:
        ----
            mock_getgrnam: Mock for grp.getgrnam function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.return_value = "testuser"

        mock_group = mock.MagicMock()
        mock_group.gr_mem = "testuser"
        mock_getgrnam.return_value = mock_group

        cli_instance._check_input_group()

    @mock.patch("os.getlogin")
    @mock.patch("grp.getgrnam")
    def test_check_input_group_user_not_in_group(
        self,
        mock_getgrnam: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group when user is not in the input group.

        Args:
        ----
            mock_getgrnam: Mock for grp.getgrnam function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.return_value = "testuser"

        mock_group = mock.MagicMock()
        mock_group.gr_mem = "otheruser"  # Setup faulty value
        mock_getgrnam.return_value = mock_group

        with pytest.raises(PermissionError):
            cli_instance._check_input_group()

    @mock.patch("os.getlogin")
    @mock.patch("grp.getgrnam")
    def test_check_input_group_empty_group(
        self,
        mock_getgrnam: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group with an empty input group.

        Args:
        ----
            mock_getgrnam: Mock for grp.getgrnam function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.return_value = "testuser"

        mock_group = mock.MagicMock()
        mock_group.gr_mem = []
        mock_getgrnam.return_value = mock_group

        with pytest.raises(PermissionError):
            cli_instance._check_input_group()

    @mock.patch("os.getlogin")
    @mock.patch("os.getenv")
    @mock.patch("grp.getgrnam")
    def test_check_input_group_getlogin_fails(
        self,
        mock_getgrnam: mock.MagicMock,
        mock_getenv: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group when os.getlogin() fails.

        Args:
        ----
            mock_getgrnam: Mock for grp.getgrnam function.
            mock_getenv: Mock for os.getenv function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.side_effect = OSError("getlogin failed")
        mock_getenv.side_effect = lambda x: {"USER": "testuser"}.get(x)

        mock_group = mock.MagicMock()
        mock_group.gr_mem = "testuser"
        mock_getgrnam.return_value = mock_group

        # Should fall back to os.getenv and not raise an exception
        cli_instance._check_input_group()

    @mock.patch("os.getlogin")
    @mock.patch("os.getenv")
    def test_check_input_group_getlogin_and_getenv_fail(
        self,
        mock_getenv: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group when both os.getlogin() and os.getenv() fail.

        Args:
        ----
            mock_getenv: Mock for os.getenv function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.side_effect = OSError("getlogin failed")
        mock_getenv.return_value = None

        with pytest.raises(PermissionError):
            cli_instance._check_input_group()

    @mock.patch("os.getlogin")
    @mock.patch("grp.getgrnam")
    def test_check_input_group_getgrnam_fails(
        self,
        mock_getgrnam: mock.MagicMock,
        mock_getlogin: mock.MagicMock,
        cli_instance: CLI,
    ) -> None:
        """Test _check_input_group when grp.getgrnam() fails.

        Args:
        ----
            mock_getgrnam: Mock for grp.getgrnam function.
            mock_getlogin: Mock for os.getlogin function.
            cli_instance: CLI instance fixture.

        """
        mock_getlogin.return_value = "testuser"
        mock_getgrnam.side_effect = KeyError("input group not found")

        # PermissionError since the input group doesn't exist
        with pytest.raises(PermissionError):
            cli_instance._check_input_group()
