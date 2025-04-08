"""The statistics page displays keystroke data in various graphs/diagrams."""

import math
from dataclasses import dataclass

import cairo
from gi.repository import Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokeStore


@dataclass
class BarConfig:
    """Configuration for drawing a bar in the chart."""

    cr: cairo.Context
    index: int
    keystroke: Keystroke
    max_count: int
    bar_width: float
    max_height: float
    base_y: float
    width: int


@dataclass
class TextConfig:
    """Configuration for drawing text."""

    cr: cairo.Context
    text: str
    x: float
    y: float
    font_size: float
    font_weight: cairo.FontWeight
    center: bool = False


@Gtk.Template(resource_path="/edu/ost/typetrace/view/statistics.ui")
class Statistics(Gtk.Box):
    """The statistics page displays keystroke data in various graphs/diagrams."""

    __gtype_name__ = "Statistics"

    carousel = Gtk.Template.Child()
    drawing_area = Gtk.Template.Child()
    line_drawing_area = Gtk.Template.Child()
    bar_count_spin = Gtk.Template.Child()
    calendar = Gtk.Template.Child()
    calendar_popover = Gtk.Template.Child()
    date_button = Gtk.Template.Child()
    clear_date_button = Gtk.Template.Child()

    def __init__(self, keystroke_store: KeystrokeStore, **kwargs) -> None:
        """Initialize the statistics page with keystroke data.

        Args:
            keystroke_store: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store
        self.selected_date = None

        # Set up bar chart
        self.drawing_area.set_draw_func(self.on_draw_bar_chart)
        self.bar_count_spin.connect("value-changed", self.on_bar_count_changed)
        self.bar_count_spin.set_range(1, 10)
        self.bar_count_spin.set_value(5)

        # Set up date filtering
        self.clear_date_button.connect("clicked", self.on_clear_date_clicked)
        self.calendar.connect("day-selected", self.on_date_selected)
        self.clear_date_button.set_sensitive(False)

    def on_bar_count_changed(self, _widget: Gtk.SpinButton) -> None:
        """Handle changes to the bar count spin button.

        Args:
            _widget: The spin button widget (unused)

        """
        self.drawing_area.queue_draw()

    def on_draw_bar_chart(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw function for the bar chart DrawingArea.

        Args:
            _area: The DrawingArea widget (unused)
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area

        """
        bar_count = int(self.bar_count_spin.get_value())
        top_keystrokes = self._get_top_keystrokes(bar_count)

        if not top_keystrokes:
            self._draw_no_data_message(cr, width, height)
            return

        self._draw_bar_chart(cr, width, height, top_keystrokes)

    def on_clear_date_clicked(self, _button: Gtk.Button) -> None:
        """Clear the date filter and show aggregated data."""
        self.selected_date = None
        self.calendar_popover.popdown()
        self.clear_date_button.set_sensitive(False)
        self.date_button.set_label("Select Date")
        self.drawing_area.queue_draw()

    def on_date_selected(self, calendar: Gtk.Calendar) -> None:
        """Handle date selection from calendar.

        Args:
            calendar: The calendar widget that triggered the event

        """
        date = calendar.get_date()
        self.selected_date = date.format("%Y-%m-%d")
        self.calendar_popover.popdown()
        self.clear_date_button.set_sensitive(True)
        self.date_button.set_label(self.selected_date)
        self.drawing_area.queue_draw()

    def _get_top_keystrokes(self, count: int) -> list[Keystroke]:
        """Get the top N keystrokes by count.

        Args:
            count: Number of top keystrokes to return

        Returns:
            List of top keystrokes sorted by count in descending order

        """
        if self.selected_date:
            keystrokes = self.keystroke_store.get_keystrokes_by_date(self.selected_date)
        else:
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
        text_config = TextConfig(
            cr=cr,
            text="No keystroke data available",
            x=(width - cr.text_extents("No keystroke data available").width) / 2,
            y=height / 2,
            font_size=16,
            font_weight=cairo.FONT_WEIGHT_BOLD,
        )
        self._draw_text(text_config)

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

        left_margin = width * 0.1
        right_margin = width * 0.1
        available_width = width - left_margin - right_margin

        bar_width = available_width / (num_bars * 1.2)

        max_height = height * 0.7  # Padding at top
        base_y = height * 0.85  # Padding bottom

        # Draw bars
        for i, keystroke in enumerate(keystrokes):
            config = BarConfig(
                cr=cr,
                index=i,
                keystroke=keystroke,
                max_count=max_count,
                bar_width=bar_width,
                max_height=max_height,
                base_y=base_y,
                width=width,
            )
            self._draw_bar(config)

        # Draw chart elements
        self._draw_baseline(cr, width, base_y)
        self._draw_axis_labels(cr, width, height, base_y)

    def _draw_bar(self, config: BarConfig) -> None:
        """Draw a single bar with its labels.

        Args:
            config: Configuration for drawing the bar

        """
        bar_height = (config.keystroke.count / config.max_count) * config.max_height

        left_margin = config.width * 0.1
        spacing = config.bar_width * 0.2
        x = left_margin + (config.index * (config.bar_width + spacing))

        y = config.base_y - bar_height

        # Draw the bar
        config.cr.set_source_rgb(0.4, 0.6, 0.8)  # Blue bars
        config.cr.rectangle(x, y, config.bar_width, bar_height)
        config.cr.fill()

        # Draw key name under bar
        self._draw_text(
            TextConfig(
                cr=config.cr,
                text=config.keystroke.key_name,
                x=x + (config.bar_width / 2),
                y=config.base_y + 15,
                font_size=10,
                font_weight=cairo.FONT_WEIGHT_NORMAL,
                center=True,
            ),
        )

        # Draw count above bar
        self._draw_text(
            TextConfig(
                cr=config.cr,
                text=str(config.keystroke.count),
                x=x + (config.bar_width / 2),
                y=y - 5,
                font_size=10,
                font_weight=cairo.FONT_WEIGHT_NORMAL,
                center=True,
            ),
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
            TextConfig(
                cr=cr,
                text="Key Name",
                x=width / 2,
                y=base_y + 35,
                font_size=12,
                font_weight=cairo.FONT_WEIGHT_BOLD,
                center=True,
            ),
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

    def _draw_text(self, config: TextConfig) -> None:
        """Draw text with the specified parameters.

        Args:
            config: Configuration for drawing text

        """
        config.cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        config.cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, config.font_weight)
        config.cr.set_font_size(config.font_size)

        x = config.x
        if config.center:
            text_width = config.cr.text_extents(config.text).width
            x = x - text_width / 2

        config.cr.move_to(x, config.y)
        config.cr.show_text(config.text)
