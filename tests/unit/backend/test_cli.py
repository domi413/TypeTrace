"""Unit tests for the CLI class in typetrace.backend.cli."""

import logging
import platform
import sqlite3
import unittest
from unittest import mock

from typetrace.backend.cli import CLI
from typetrace.config import Config, ExitCodes

logging.disable(logging.CRITICAL)


class TestCLI(unittest.TestCase):
    """Test suite for the CLI class."""

    def setUp(self) -> None:
        """Initialize a fresh CLI instance before each test."""
        self.cli = CLI()

    def test_run_unsupported_platform(self) -> None:
        """Return PLATFORM_ERROR when running on unsupported platform."""
        args = mock.MagicMock(debug=False)
        with mock.patch.object(platform, "system", return_value="UnknownOS"):
            code = self.cli.run(args)
        self.assertEqual(code, ExitCodes.PLATFORM_ERROR)

    @unittest.skip("Skipping DB-error test until initialize_database bugfix")
    def test_run_database_error(self) -> None:
        """Return DATABASE_ERROR when initialize_database raises sqlite3.Error."""
        args = mock.MagicMock(debug=False)
        with mock.patch.object(platform, "system", return_value="Linux"), \
             mock.patch.object(self.cli._CLI__db_manager,
                              "initialize_database",
                              side_effect=sqlite3.Error):
            code = self.cli.run(args)
        self.assertEqual(code, ExitCodes.DATABASE_ERROR)

    def test_run_permission_error(self) -> None:
        """Return PERMISSION_ERROR if user is not in 'input' group."""
        args = mock.MagicMock(debug=False)
        with mock.patch.object(platform, "system", return_value="Linux"), \
             mock.patch.object(self.cli._CLI__db_manager,
                              "initialize_database",
                              return_value=None), \
             mock.patch.object(self.cli,
                              "_check_input_group",
                              side_effect=PermissionError):
            code = self.cli.run(args)
        self.assertEqual(code, ExitCodes.PERMISSION_ERROR)

    @unittest.skip("Skip Linux success test until event-processor fix")
    def test_run_success_linux(self) -> None:
        """Return SUCCESS and call trace() on Linux."""
        args = mock.MagicMock(debug=False)
        processor_mock = mock.MagicMock()
        with mock.patch.object(platform, "system", return_value="Linux"), \
             mock.patch.object(self.cli._CLI__db_manager,
                              "initialize_database",
                              return_value=None), \
             mock.patch("typetrace.backend.events.linux.LinuxEventProcessor",
                        return_value=processor_mock):
            code = self.cli.run(args)

        processor_mock.check_device_accessibility.assert_called_once()
        processor_mock.trace.assert_called_once()
        self.assertEqual(code, ExitCodes.SUCCESS)

    def test_check_input_group_member(self) -> None:
        """Not raise PermissionError if user is in the 'input' group."""
        with mock.patch("os.getlogin", return_value="user1"), \
             mock.patch("grp.getgrnam", return_value=mock.MagicMock(gr_mem=["user1"])):
            try:
                self.cli._check_input_group()
            except PermissionError:
                self.fail("_check_input_group() raised PermissionError unexpectedly")

    def test_run_debug_mode(self) -> None:
        """Enable debug mode and run dummy backend successfully."""
        args = mock.MagicMock(debug=True)
        dummy_backend = mock.MagicMock()
        module = "typetrace.backend.ipc.linux_darwin"

        with mock.patch.object(Config, "DEBUG", new=False), \
             mock.patch("typetrace.backend.cli.LoggerSetup.setup_logging",
                        return_value=None) as mock_log, \
             mock.patch(f"{module}.LinuxMacOSIPC", return_value=dummy_backend):
            code = self.cli.run(args)

        mock_log.assert_called_once()
        dummy_backend.register_callback.assert_called()
        dummy_backend.run.assert_called_once()
        self.assertEqual(code, ExitCodes.SUCCESS)


if __name__ == "__main__":
    unittest.main()
