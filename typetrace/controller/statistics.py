"""The statistics page displays keystroke data in various graphs/diagrams."""

from gi.repository import Gtk

from typetrace.model.keystrokes import KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/statistics.ui")
class Statistics(Gtk.Box):
    """The statistics page displays keystroke data in various graphs/diagrams."""

    __gtype_name__ = "Statistics"

    drawing_area = Gtk.Template.Child()

    def __init__(self, keystroke_store: KeystrokeStore, **kwargs) -> None:
        """Initialize the statistics page with keystroke data.

        Args:
            keystroke_store: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store

        self.drawing_area.set_draw_func(self.on_draw)

    def on_draw(self, area, cr, width, height):
        """Draw function for the DrawingArea.

        Args:
            area: The DrawingArea widget
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area

        """
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
