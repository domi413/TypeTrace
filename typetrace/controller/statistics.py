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
        # Get keystrokes and sort by count descending
        keystrokes = self.keystroke_store.get_all_keystrokes()
        keystrokes.sort(key=lambda k: k.count, reverse=True)

        top_keystrokes = keystrokes[:5]

        # If no keystrokes, display message
        if not top_keystrokes:
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(16)
            message = "No keystroke data available"
            text_width = cr.text_extents(message).width
            cr.move_to((width - text_width) / 2, height / 2)
            cr.show_text(message)
            return

        # Max count for scaling
        max_count = top_keystrokes[0].count if top_keystrokes else 1

        # Chart dimensions
        num_bars = len(top_keystrokes)
        bar_width = width / (num_bars * 2)  # Padding between bars
        max_height = height * 0.7  # Padding at top
        base_y = height * 0.85  # Padding bottom

        # Draw bars
        for i, keystroke in enumerate(top_keystrokes):
            bar_height = (keystroke.count / max_count) * max_height

            x = width * 0.1 + (i * bar_width * 2)  # Space bars evenly with left padding
            y = base_y - bar_height

            cr.set_source_rgb(0.4, 0.6, 0.8)  # Blue bars
            cr.rectangle(x, y, bar_width, bar_height)
            cr.fill()

            # Add key name under bar
            cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
            cr.select_font_face(
                "Sans",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL,
            )
            cr.set_font_size(10)
            key_name = keystroke.key_name
            text_width = cr.text_extents(key_name).width
            text_x = x + (bar_width - text_width) / 2
            text_y = base_y + 15
            cr.move_to(text_x, text_y)
            cr.show_text(key_name)

            # Add count above bar
            count_text = str(keystroke.count)
            text_width = cr.text_extents(count_text).width
            text_x = x + (bar_width - text_width) / 2
            text_y = y - 5
            cr.move_to(text_x, text_y)
            cr.show_text(count_text)

        # Add baseline
        cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray
        cr.set_line_width(2)
        cr.move_to(0, base_y)
        cr.line_to(width, base_y)
        cr.stroke()

        # Add axis labels
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text color for text
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(12)

        # X-axis label
        x_label = "Key Name"
        x_label_width = cr.text_extents(x_label).width
        x_label_x = width / 2 - x_label_width / 2
        x_label_y = base_y + 35
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
