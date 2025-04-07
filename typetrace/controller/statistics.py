"""The statistics page displays keystroke data in various graphs/diagrams."""

import math

import cairo
from gi.repository import Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokeStore


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

    def on_draw(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw function for the DrawingArea.

        Args:
            _area: The DrawingArea widget (unused)
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area

        """
        top_keystrokes = self._get_top_keystrokes(5)

        if not top_keystrokes:
            self._draw_no_data_message(cr, width, height)
            return

        self._draw_bar_chart(cr, width, height, top_keystrokes)

    def _get_top_keystrokes(self, count: int) -> list[Keystroke]:
        """Get the top N keystrokes by count.

        Args:
            count: Number of top keystrokes to return

        Returns:
            List of top keystrokes sorted by count in descending order

        """
        keystrokes = self.keystroke_store.get_all_keystrokes()
        keystrokes.sort(key=lambda k: k.count, reverse=True)
        return keystrokes[:count]

    def _draw_no_data_message(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw a message when no keystroke data is available.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area

        """
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(16)
        message = "No keystroke data available"
        text_width = cr.text_extents(message).width
        cr.move_to((width - text_width) / 2, height / 2)
        cr.show_text(message)

    def _draw_bar_chart(
        self,
        cr: cairo.Context,
        width: int,
        height: int,
        keystrokes: list[Keystroke],
    ) -> None:
        """Draw a bar chart with the given keystrokes.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area
            keystrokes: List of keystrokes to display

        """
        # Max count for scaling
        max_count = keystrokes[0].count if keystrokes else 1

        # Chart dimensions
        num_bars = len(keystrokes)
        bar_width = width / (num_bars * 2)  # Padding between bars
        max_height = height * 0.7  # Padding at top
        base_y = height * 0.85  # Padding bottom

        # Draw bars
        for i, keystroke in enumerate(keystrokes):
            self._draw_bar(
                cr,
                i,
                keystroke,
                max_count,
                bar_width,
                max_height,
                base_y,
                width,
            )

        # Draw chart elements
        self._draw_baseline(cr, width, base_y)
        self._draw_axis_labels(cr, width, height, base_y)

    def _draw_bar(
        self,
        cr: cairo.Context,
        index: int,
        keystroke: Keystroke,
        max_count: int,
        bar_width: float,
        max_height: float,
        base_y: float,
        width: int,
    ) -> None:
        """Draw a single bar with its labels.

        Args:
            cr: Cairo context for drawing
            index: Index of the bar
            keystroke: Keystroke data for this bar
            max_count: Maximum count for scaling
            bar_width: Width of each bar
            max_height: Maximum height of bars
            base_y: Y-coordinate of the baseline
            width: Width of the drawing area

        """
        bar_height = (keystroke.count / max_count) * max_height

        x = width * 0.1 + (index * bar_width * 2)  # Space bars evenly with left padding
        y = base_y - bar_height

        # Draw the bar
        cr.set_source_rgb(0.4, 0.6, 0.8)  # Blue bars
        cr.rectangle(x, y, bar_width, bar_height)
        cr.fill()

        # Draw key name under bar
        self._draw_text(
            cr,
            keystroke.key_name,
            x + (bar_width / 2),
            base_y + 15,
            10,
            cairo.FONT_WEIGHT_NORMAL,
            center=True,
        )

        # Draw count above bar
        self._draw_text(
            cr,
            str(keystroke.count),
            x + (bar_width / 2),
            y - 5,
            10,
            cairo.FONT_WEIGHT_NORMAL,
            center=True,
        )

    def _draw_baseline(self, cr: cairo.Context, width: int, base_y: float) -> None:
        """Draw the baseline of the chart.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            base_y: Y-coordinate of the baseline

        """
        cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray
        cr.set_line_width(2)
        cr.move_to(0, base_y)
        cr.line_to(width, base_y)
        cr.stroke()

    def _draw_axis_labels(
        self,
        cr: cairo.Context,
        width: int,
        height: int,
        base_y: float,
    ) -> None:
        """Draw the axis labels for the chart.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area
            base_y: Y-coordinate of the baseline

        """
        # X-axis label
        self._draw_text(
            cr,
            "Key Name",
            width / 2,
            base_y + 35,
            12,
            cairo.FONT_WEIGHT_BOLD,
            center=True,
        )

        # Y-axis label
        y_label_width = cr.text_extents("Count").width
        y_label_x = 10
        y_label_y = height / 2 + y_label_width / 2

        cr.save()
        cr.translate(y_label_x, y_label_y)
        cr.rotate(-math.pi / 2)  # Rotate 90 degrees
        cr.move_to(0, 0)
        cr.show_text("Count")
        cr.restore()

    def _draw_text(
        self,
        cr: cairo.Context,
        text: str,
        x: float,
        y: float,
        font_size: float,
        font_weight: cairo.FontWeight,
        *,
        center: bool = False,
    ) -> None:
        """Draw text with the specified parameters.

        Args:
            cr: Cairo context for drawing
            text: Text to draw
            x: X-coordinate
            y: Y-coordinate
            font_size: Font size
            font_weight: Font weight
            center: Whether to center the text horizontally

        """
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, font_weight)
        cr.set_font_size(font_size)

        if center:
            text_width = cr.text_extents(text).width
            x = x - text_width / 2

        cr.move_to(x, y)
        cr.show_text(text)
