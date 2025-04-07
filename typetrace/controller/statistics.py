"""The statistics page displays keystroke data in various graphs/diagrams."""

import math

import cairo
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
        num_bars = 5
        bar_width = width / (num_bars * 2)  # Padding between bars
        max_height = height * 0.8  # Padding at top
        base_y = height * 0.9  # Padding bottom

        # Draw bars
        cr.set_source_rgb(0.4, 0.6, 0.8)  # Blue bars
        for i in range(num_bars):
            bar_height = max_height  # 100% of max_height
            x = width * 0.1 + (i * bar_width * 2)  # Space bars evenly with left padding
            y = base_y - bar_height

            cr.rectangle(x, y, bar_width, bar_height)  # Draw the bar
            cr.fill()

        # Add baseline
        cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray
        cr.set_line_width(2)
        cr.move_to(width * 0.05, base_y)
        cr.line_to(width * 0.95, base_y)
        cr.stroke()

        # Add axis labels
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text color for text
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12)

        # X-axis label
        x_label = "Key Name"
        x_label_width = cr.text_extents(x_label).width
        x_label_x = width / 2 - x_label_width / 2
        x_label_y = base_y + 25
        cr.move_to(x_label_x, x_label_y)
        cr.show_text(x_label)

        # Y-axis label
        y_label = "Count"
        y_label_width = cr.text_extents(y_label).width
        y_label_x = 10
        y_label_y = height / 2 + y_label_width / 2
        cr.save()
        cr.translate(y_label_x, y_label_y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text(y_label)
        cr.restore()
