import pytest
import sys
from unittest.mock import MagicMock, patch


# Fixture to mock gi.repository for all tests
@pytest.fixture(autouse=True)
def mock_gi():
    """Mock gi.repository to allow tests to run without PyGObject dependencies."""
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):
        mock_repository.Gtk = MagicMock()
        mock_repository.GObject = MagicMock()
        mock_repository.Gtk.Box = MagicMock()
        mock_repository.Gtk.Label = MagicMock()

        # Mock Gtk.Template to handle decorator usage and Child method
        class MockTemplate:
            def __init__(self, *args, **kwargs):
                # Accept decorator arguments like resource_path without errors
                pass

            def __call__(self, cls):
                # Return the class unchanged when used as a decorator
                return cls

            @staticmethod
            def Child(name):
                # Simulate retrieving a child widget (e.g., keyboard_container)
                return MagicMock()

        # Assign the mock template to Gtk.Template
        mock_repository.Gtk.Template = MockTemplate

        yield mock_repository


def test_build_keyboard(mocker, mock_gi):
    """Test the dynamic creation of the keyboard layout in the Heatmap class."""
    from typetrace.model.keystrokes import KeystrokeStore
    from typetrace.controller.heatmap import Heatmap

    # Create a mock KeystrokeStore object
    mock_store = mocker.Mock(spec=KeystrokeStore)

    # Instantiate the Heatmap class with the mock store and 'en_US' layout
    heatmap = Heatmap(keystroke_store=mock_store, layout="en_US")

    # Call the internal method to build the keyboard layout
    heatmap._build_keyboard()

    # Verify the number of Gtk.Box and Gtk.Label widgets created matches the layout
    layout = heatmap.KEYBOARD_LAYOUTS["en_US"]
    expected_boxes = len(layout)  # Number of rows in the layout
    expected_labels = sum(len(row) for row in layout)  # Total keys in the layout
    assert mock_gi.Gtk.Box.call_count == expected_boxes
    assert mock_gi.Gtk.Label.call_count == expected_labels
