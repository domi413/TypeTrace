"""Window module for the Typetrace application."""

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/edu/ost/typetrace/view/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    """Main application window class for Typetrace.

    Provides the user interface for the application.
    """

    __gtype_name__ = "TypetraceWindow"

    # Template child for accessing the label widget
    label = Gtk.Template.Child()

    def __init__(self, **kwargs) -> None:
        """Initialize the application window.

        Args:
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
