"""The statistics page displays keystroke data in various graphs/diagrams."""

# TODO: We should completely rewrite this but use the information we gained from this implementation
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import cairo
from gi.repository import Adw, Gio, GLib, Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokeStore


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
        self.style_manager = Adw.StyleManager.get_default()

        # Set up keystrokes over time chart (first page)
        self.drawing_area.set_draw_func(self._draw_keystrokes_over_time)

        # Set up pie chart (second page)
        self.line_drawing_area.set_draw_func(self.on_draw_pie_chart)
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
        self.line_drawing_area.queue_draw()

    def on_clear_date_clicked(self, _button: Gtk.Button) -> None:
        """Clear the date filter and show aggregated data."""
        self.selected_date = None
        self.calendar_popover.popdown()
        self.clear_date_button.set_sensitive(False)
        self.date_button.set_label("Select Date")
        self.line_drawing_area.queue_draw()

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
        self.line_drawing_area.queue_draw()

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

    def _draw_no_data_message(
        self, cr: cairo.Context, width: int, height: int, text_color=(1.0, 1.0, 1.0)
    ) -> None:
        """Draw a message when no keystroke data is available.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area
            text_color: Color of the text

        """
        text_config = TextConfig(
            cr=cr,
            text="No keystroke data available",
            x=(width - cr.text_extents("No keystroke data available").width) / 2,
            y=height / 2,
            font_size=16,
            font_weight=cairo.FONT_WEIGHT_BOLD,
        )
        self._draw_text(text_config, text_color)

    def _draw_text(self, config: TextConfig, color=(1.0, 1.0, 1.0)) -> None:
        """Draw text with the specified parameters.

        Args:
            config: Configuration for drawing text
            color: Text color (RGB)

        """
        config.cr.set_source_rgb(*color)  # Text color
        config.cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, config.font_weight)
        config.cr.set_font_size(config.font_size)

        x = config.x
        if config.center:
            text_width = config.cr.text_extents(config.text).width
            x = x - text_width / 2

        config.cr.move_to(x, config.y)
        config.cr.show_text(config.text)

    def on_draw_pie_chart(
        self,
        _area: Gtk.DrawingArea,
        cr: cairo.Context,
        width: int,
        height: int,
    ) -> None:
        """Draw function for the pie chart DrawingArea.

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

        self._draw_pie_chart(cr, width, height, top_keystrokes)

    def _draw_pie_chart(
        self,
        cr: cairo.Context,
        width: int,
        height: int,
        keystrokes: list[Keystroke],
    ) -> None:
        """Draw a pie chart with the given keystrokes.

        Args:
            cr: Cairo context for drawing
            width: Width of the drawing area
            height: Height of the drawing area
            keystrokes: List of keystrokes to display

        """
        # Colors for the pie slices
        colors = [
            (0.4, 0.6, 0.8),  # Blue
            (0.8, 0.4, 0.4),  # Red
            (0.4, 0.8, 0.4),  # Green
            (0.8, 0.8, 0.4),  # Yellow
            (0.6, 0.4, 0.8),  # Purple
            (0.8, 0.6, 0.4),  # Orange
            (0.4, 0.8, 0.8),  # Cyan
            (0.8, 0.4, 0.8),  # Magenta
            (0.5, 0.5, 0.5),  # Gray
            (0.7, 0.7, 0.9),  # Light purple
        ]

        # Title
        cr.set_source_rgb(1.0, 1.0, 1.0)  # White text
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(16)
        title = "Top Keystroke Distribution"
        text_extents = cr.text_extents(title)
        cr.move_to((width - text_extents.width) / 2, 30)
        cr.show_text(title)

        # Calculate total keystrokes
        total_count = sum(keystroke.count for keystroke in keystrokes)
        if total_count == 0:
            self._draw_no_data_message(cr, width, height)
            return

        # Pie chart dimensions
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) * 0.35  # Adjust radius to fit the chart

        # Draw pie slices
        start_angle = -math.pi / 2  # Start from top (270 degrees)
        legend_y = height * 0.15  # Starting Y position for legend

        for i, keystroke in enumerate(keystrokes):
            # Calculate slice angle based on percentage
            slice_percentage = keystroke.count / total_count
            slice_angle = 2 * math.pi * slice_percentage

            # Draw the slice
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.move_to(center_x, center_y)
            cr.arc(center_x, center_y, radius, start_angle, start_angle + slice_angle)
            cr.close_path()
            cr.fill()

            # Calculate position for percentage label
            label_angle = start_angle + slice_angle / 2
            label_distance = radius * 0.7  # Position inside the slice
            label_x = center_x + math.cos(label_angle) * label_distance
            label_y = center_y + math.sin(label_angle) * label_distance

            # Only show percentage if slice is big enough
            if slice_percentage > 0.05:  # More than 5%
                percentage_text = f"{slice_percentage:.1%}"
                cr.set_source_rgb(1, 1, 1)  # White text
                cr.select_font_face(
                    "Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
                )
                cr.set_font_size(12)
                text_extents = cr.text_extents(percentage_text)
                cr.move_to(
                    label_x - text_extents.width / 2, label_y + text_extents.height / 2
                )
                cr.show_text(percentage_text)

            # Draw legend items
            legend_x = width * 0.75
            legend_box_size = 15

            # Legend color box
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.rectangle(
                legend_x - 100, legend_y + i * 25, legend_box_size, legend_box_size
            )
            cr.fill()

            # Legend text
            cr.set_source_rgb(1, 1, 1)  # White text
            cr.select_font_face(
                "Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL
            )
            cr.set_font_size(12)
            legend_text = (
                f"{keystroke.key_name}: {keystroke.count} ({slice_percentage:.1%})"
            )
            cr.move_to(legend_x - 80, legend_y + i * 25 + 12)
            cr.show_text(legend_text)

            # Update angle for next slice
            start_angle += slice_angle

    # --- Keystrokes Over Time Chart (First Page) ---

    def _draw_keystrokes_over_time(self, area, cr, width, height):
        """Draw the keystrokes over time graph.

        This is the main drawing function connected to the DrawingArea.

        Args:
            area: The Gtk.DrawingArea being drawn
            cr: The Cairo context to draw with
            width: Width of the drawing area
            height: Height of the drawing area

        """
        # Get theme status
        # TODO: can we clean up this method?
        is_dark = self.style_manager.get_dark()
        is_high_contrast = self.style_manager.get_high_contrast()

        # Get the accent color for the chart
        accent_color = self._get_accent_color(is_dark)

        # Setup colors based on theme
        colors = self._determine_colors(is_dark, is_high_contrast, accent_color)

        # Calculate dimensions
        # TODO: Doesnt seem to work?!
        padding = 40
        graph_width = width - padding * 2
        graph_height = height - padding * 2

        # Get data to display
        keystroke_data = self._get_keystroke_data()

        if not keystroke_data:
            # Show message if no data available
            self._draw_no_data_message(cr, width, height, colors["text"])
            return

        # Calculate max value for y-axis
        max_value = self._calculate_max_value(keystroke_data)

        # Draw chart components
        self._draw_grid(
            cr,
            width,
            height,
            padding,
            graph_width,
            graph_height,
            max_value,
            keystroke_data,
            colors,
        )
        points = self._draw_line_chart(
            cr, keystroke_data, padding, graph_width, graph_height, max_value, colors
        )
        self._draw_data_points(cr, points, keystroke_data, colors)
        self._draw_day_labels(
            cr, keystroke_data, points, width, height, padding, colors["text"]
        )
        self._draw_title(cr, width, padding, colors["text"])
        self._draw_axes(cr, width, height, padding, colors["text"])

    def _get_accent_color(self, is_dark):
        """Get the accent color from GNOME settings or a fallback."""
        # TODO: Rather use: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/method.StyleManager.get_accent_color.html
        try:
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            accent_name = settings.get_string("accent-color")

            # GNOME accent colors map
            accent_colors = {
                "blue": (0.2, 0.5, 0.9),
                "green": (0.3, 0.8, 0.2),
                "yellow": (0.9, 0.8, 0.2),
                "orange": (0.9, 0.6, 0.2),
                "red": (0.9, 0.2, 0.2),
                "magenta": (0.9, 0.2, 0.9),
                "purple": (0.7, 0.3, 0.9),
                "brown": (0.7, 0.5, 0.4),
                "gray": (0.5, 0.5, 0.5),
            }

            if accent_name in accent_colors:
                return accent_colors[accent_name]
        except (GLib.Error, AttributeError):
            pass
        # Default accent color
        return (0.3, 0.6, 1.0) if is_dark else (0.2, 0.5, 0.9)

    def _determine_colors(self, is_dark, is_high_contrast, accent_color):
        """Determine the color scheme based on theme settings."""
        line_color = accent_color

        # In high contrast mode, use higher contrast colors
        if is_high_contrast:
            text_color = (1.0, 1.0, 1.0) if is_dark else (0.0, 0.0, 0.0)
            grid_color = (0.7, 0.7, 0.7) if is_dark else (0.3, 0.3, 0.3)
            fill_color = (*accent_color, 0.4)  # More opaque
        else:
            text_color = (0.9, 0.9, 0.9) if is_dark else (0.2, 0.2, 0.2)
            grid_color = (0.3, 0.3, 0.3) if is_dark else (0.8, 0.8, 0.8)
            fill_color = (*accent_color, 0.2)  # Semi-transparent

        return {
            "line": line_color,
            "fill": fill_color,
            "text": text_color,
            "grid": grid_color,
        }

    def _calculate_max_value(self, keystroke_data):
        """Calculate the maximum value for the y-axis with headroom."""
        max_value = max(item["count"] for item in keystroke_data)
        return max_value * 1.1 if max_value > 0 else 10

    def _draw_grid(
        self,
        cr,
        width,
        height,
        padding,
        graph_width,
        graph_height,
        max_value,
        keystroke_data,
        colors,
    ):
        """Draw the grid lines and labels."""
        num_lines = 5
        for i in range(num_lines + 1):
            y = padding + graph_height - (i * graph_height / num_lines)

            # Draw the grid line
            cr.set_source_rgba(*colors["grid"], 0.5)
            cr.set_line_width(0.5)
            cr.move_to(padding, y)
            cr.line_to(width - padding, y)
            cr.stroke()

            # Label the grid line with value
            value = max_value * (i / num_lines)
            self._draw_grid_label_y_axis(
                cr,
                str(int(value)),
                padding,
                y,
                colors["text"],
            )

        # Draw vertical grid lines
        num_days = len(keystroke_data)
        for i in range(num_days):
            x = (
                padding + (i * graph_width / (num_days - 1))
                if num_days > 1
                else padding
            )
            cr.set_source_rgba(*colors["grid"], 0.5)
            cr.move_to(x, padding)
            cr.line_to(x, height - padding)
            cr.stroke()

    def _draw_grid_label_y_axis(self, cr, value, padding, y, text_color):
        """Draw a grid label at the specified position using 100-unit increments."""
        cr.set_source_rgba(*text_color, 1)
        cr.select_font_face("Sans", 0, 0)  # Normal slant, normal weight
        cr.set_font_size(15)

        # Round the value to the nearest 100
        label = str(int(round(float(value) / 100) * 100))

        # Calculate text dimensions
        text_extents = cr.text_extents(label)
        cr.move_to(padding - text_extents.width - 5, y + text_extents.height / 2 - 2)
        cr.show_text(label)

    def _draw_line_chart(
        self, cr, keystroke_data, padding, graph_width, graph_height, max_value, colors
    ):
        """Draw the line chart with filled area beneath."""
        # Setup line properties
        cr.set_line_width(2)
        cr.set_source_rgba(*colors["line"], 1)

        # Variables for path creation
        points = []
        num_days = len(keystroke_data)

        # Calculate points for the line
        for i, item in enumerate(keystroke_data):
            x = (
                padding + (i * graph_width / (num_days - 1))
                if num_days > 1
                else padding
            )
            y = (
                padding + graph_height - (item["count"] / max_value * graph_height)
                if max_value > 0
                else padding + graph_height
            )
            points.append((x, y))

        if not points:
            return []

        # Start a new path at the first point
        cr.move_to(*points[0])

        # Draw a smooth curve through the points
        if len(points) > 1:
            # For each segment, calculate control points for smooth curves
            for i in range(1, len(points)):
                # Previous, current, and next points
                x0, y0 = points[i - 1]
                x1, y1 = points[i]

                # Calculate control point distance (tension)
                # Lower values = smoother curve
                tension = 0.4
                cp_dist_x = (x1 - x0) * tension

                # For smoother transition between points
                if i < len(points) - 1:
                    # Get the next point for better curve shaping
                    x2, y2 = points[i + 1]
                    # Control points for current segment
                    cp1_x = x0 + cp_dist_x
                    cp1_y = y0
                    cp2_x = x1 - cp_dist_x
                    cp2_y = y1
                else:
                    # Last segment
                    cp1_x = x0 + cp_dist_x
                    cp1_y = y0
                    cp2_x = x1 - cp_dist_x
                    cp2_y = y1

                # Draw the cubic bezier curve segment
                cr.curve_to(cp1_x, cp1_y, cp2_x, cp2_y, x1, y1)

        # Save the path for filling
        cr.stroke_preserve()

        # Continue the path for fill area
        last_x = points[-1][0]
        last_y = padding + graph_height
        cr.line_to(last_x, last_y)  # Bottom right
        cr.line_to(padding, last_y)  # Bottom left
        cr.close_path()

        # Fill area under the curve
        cr.set_source_rgba(*colors["fill"])
        cr.fill()

        return points

    def _draw_data_points(self, cr, points, keystroke_data, colors):
        """Draw data points with values on the chart."""
        for i, (x, y) in enumerate(points):
            # Draw the point
            cr.set_source_rgba(*colors["line"], 1)
            cr.arc(x, y, 3, 0, 2 * math.pi)
            cr.fill()

            # Draw count value above point if non-zero
            count = keystroke_data[i]["count"]
            if count > 0:
                count_label = str(count)
                cr.set_source_rgba(*colors["text"], 1)
                cr.select_font_face("Sans", 0, 0)  # Normal slant, normal weight
                cr.set_font_size(15)
                text_extents = cr.text_extents(count_label)
                cr.move_to(x - text_extents.width / 2, y - 10)
                cr.show_text(count_label)

    def _draw_day_labels(
        self, cr, keystroke_data, points, width, height, padding, text_color
    ):
        """Draw day labels along the x-axis."""
        cr.set_source_rgba(*text_color, 1)
        cr.select_font_face("Sans", 0, 0)  # Normal slant, normal weight
        cr.set_font_size(15)

        for i, (x, _) in enumerate(points):
            day_label = keystroke_data[i]["date"]
            text_extents = cr.text_extents(day_label)

            # Position text centered under the data point
            text_x = x
            text_y = height - padding + 15

            # Draw rotated text for dates
            cr.save()
            cr.move_to(text_x - text_extents.width / 2, text_y)
            cr.show_text(day_label)  # No rotation, directly below the point
            cr.restore()

    def _draw_title(self, cr, width, padding, text_color):
        """Draw the chart title."""
        cr.set_source_rgba(*text_color, 1)
        cr.select_font_face("Sans", 0, 1)  # Normal slant, bold weight
        cr.set_font_size(14)
        title = "Daily Keystroke Count"
        text_extents = cr.text_extents(title)
        cr.move_to(width / 2 - text_extents.width / 2, padding - 20)
        cr.show_text(title)

    def _draw_axes(self, cr, width, height, padding, text_color):
        """Draw the x and y axes."""
        cr.set_source_rgba(*text_color, 1)
        cr.set_line_width(2)

        # Y-axis
        cr.move_to(padding, padding)
        cr.line_to(padding, height - padding)
        cr.stroke()

        # X-axis
        cr.move_to(padding, height - padding)
        cr.line_to(width - padding, height - padding)
        cr.stroke()

    def _get_keystroke_data(self):
        """Get processed keystroke data for the past 7 days from the latest date in data."""
        # Get all keystrokes
        keystrokes = self.keystroke_store.get_all_keystrokes()
        if not keystrokes:
            return []

        # Parse all valid dates from keystroke data
        valid_dates = []
        for k in keystrokes:
            try:
                parsed_date = datetime.fromisoformat(k.date).date()
                valid_dates.append(
                    (parsed_date, k.date),
                )  # Store both parsed and original
            except ValueError:
                continue  # Skip invalid dates

        if not valid_dates:
            return []

        # Find the latest date
        latest_parsed_date, latest_date_str = max(valid_dates, key=lambda x: x[0])

        # Create data structure for 7 days (latest and 6 days before)
        data = {}
        for i in range(7):
            day = latest_parsed_date - timedelta(days=6 - i)
            day_iso = day.isoformat()
            data[day_iso] = {"date": day.strftime("%b %d"), "count": 0}

        # Create a mapping from original date strings to parsed date strings
        date_mapping = {
            original: parsed.isoformat() for parsed, original in valid_dates
        }

        # Count keystrokes by date
        for k in keystrokes:
            # First check if the original date string is directly in our window
            if k.date in data:
                data[k.date]["count"] += k.count
            # Otherwise try to use the parsed version if available
            elif k.date in date_mapping and date_mapping[k.date] in data:
                data[date_mapping[k.date]]["count"] += k.count

        # Return data as sorted list
        return [data[key] for key in sorted(data)]
