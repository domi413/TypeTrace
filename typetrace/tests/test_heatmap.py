import pytest
import sys
from unittest.mock import MagicMock, patch


# Fixture to mock gi.repository for all tests
@pytest.fixture(autouse=True)
def mock_gi():
    """Mock gi.repository to allow tests without PyGObject dependencies."""
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):
        mock_repository.Gtk = MagicMock()
        mock_repository.GObject = MagicMock()
        mock_repository.Gtk.Box = MagicMock()
        mock_repository.Gtk.Label = MagicMock()

        class MockTemplate:
            def __init__(self, *args, **kwargs):
                # Accept decorator args like resource_path without error
                pass

            def __call__(self, cls):
                return cls

            @staticmethod
            def Child(name):
                return MagicMock()

        mock_repository.Gtk.Template = MockTemplate

        yield mock_repository


def test_build_keyboard(mocker, mock_gi):
    """Test dynamic creation of keyboard layout in the Heatmap class."""
    from typetrace.model.keystrokes import KeystrokeStore
    from typetrace.controller.heatmap import Heatmap

    # Create a mock KeystrokeStore object
    mock_store = mocker.Mock(spec=KeystrokeStore)

    # Create Heatmap instance with mock store and layout
    heatmap = Heatmap(
        keystroke_store=mock_store,
        layout="en_US",
    )

    # Call method to build the keyboard layout
    heatmap._build_keyboard()

    layout = heatmap.KEYBOARD_LAYOUTS["en_US"]
    expected_boxes = len(layout)
    expected_labels = sum(len(row) for row in layout)

    assert mock_gi.Gtk.Box.call_count == expected_boxes
    assert mock_gi.Gtk.Label.call_count == expected_labels
