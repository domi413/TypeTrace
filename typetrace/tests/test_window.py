import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_gi(mocker):
    """Mock gi.repository to allow tests to run without PyGObject dependencies."""
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):

        class MockAdwApplicationWindow:
            def __init__(self, *args, **kwargs):
                pass

        mock_repository.Adw = MagicMock()
        mock_repository.Adw.ApplicationWindow = MockAdwApplicationWindow

        mock_repository.Gtk = MagicMock()
        mock_repository.Gtk.Label = MagicMock()
        mock_repository.Gtk.Template = MagicMock()

        mock_heatmap_module = MagicMock()
        mock_verbose_module = MagicMock()
        mock_heatmap_class = MagicMock()
        mock_verbose_class = MagicMock()
        mock_heatmap_module.Heatmap = mock_heatmap_class
        mock_verbose_module.Verbose = mock_verbose_class

        with patch.dict(
            sys.modules,
            {
                "typetrace.controller.heatmap": mock_heatmap_module,
                "typetrace.controller.verbose": mock_verbose_module,
            },
        ):

            class MockTemplate:
                def __init__(self, *args, **kwargs):
                    pass

                def __call__(self, cls):
                    return cls

                @staticmethod
                def Child(name):
                    if name == "view_switcher":
                        return MagicMock()
                    elif name == "stack":
                        mock_stack = MagicMock()

                        def add_titled_side_effect(*args, **kwargs):
                            return MagicMock()

                        mock_stack.add_titled.side_effect = add_titled_side_effect
                        return mock_stack
                    return MagicMock()

            mock_repository.Gtk.Template = MockTemplate

            yield mock_repository, mock_heatmap_class, mock_verbose_class


def test_stack_page_addition(mocker, mock_gi):
    """Test adding pages to the stack in TypetraceWindow."""
    from typetrace.model.keystrokes import KeystrokeStore
    from typetrace.controller.window import TypetraceWindow

    mock_repository, mock_heatmap_class, mock_verbose_class = mock_gi

    mock_store = mocker.Mock(spec=KeystrokeStore)
    window = TypetraceWindow(keystroke_store=mock_store)

    window.stack.reset_mock()

    mock_page = mocker.Mock()
    window.stack.add_titled(mock_page, "test_page", "Test Page")

    window.stack.add_titled.assert_called_once_with(mock_page, "test_page", "Test Page")


def test_view_switcher_setup(mocker, mock_gi):
    """Test setting up the view switcher in TypetraceWindow."""
    from typetrace.model.keystrokes import KeystrokeStore
    from typetrace.controller.window import TypetraceWindow

    mock_repository, mock_heatmap_class, mock_verbose_class = mock_gi

    mock_store = mocker.Mock(spec=KeystrokeStore)
    window = TypetraceWindow(keystroke_store=mock_store)

    window.view_switcher.reset_mock()

    mock_stack = mocker.Mock()
    window.view_switcher.set_stack(mock_stack)

    window.view_switcher.set_stack.assert_called_once_with(mock_stack)
