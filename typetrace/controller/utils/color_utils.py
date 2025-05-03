"""Utility functions for color manipulation."""

from __future__ import annotations

import colorsys
import logging
from abc import ABC, abstractmethod
from typing import Final, final, override

from gi.repository import Adw, Gdk, Gio

logger = logging.getLogger(__name__)


def parse_color_string(color_str: str) -> Gdk.RGBA:
    """Parse a color string into a Gdk.RGBA object.

    Handles formats like "rgb(r,g,b)" and standard Gdk color names/formats.

    Args:
    ----
        color_str: String representation of a color (e.g., "rgb(0,0,255)").

    Returns:
    -------
        Gdk.RGBA object. Returns blue as a default if parsing fails.

    """
    rgba = Gdk.RGBA()
    if color_str.startswith("rgb("):
        try:
            r, g, b = map(int, color_str[4:-1].split(","))
            rgba.red = r / 255.0
            rgba.green = g / 255.0
            rgba.blue = b / 255.0
            rgba.alpha = 1.0
        except ValueError:
            rgba.parse("blue")
            rgba.alpha = 1.0
    else:
        parsed = rgba.parse(color_str)
        if not parsed:
            rgba.parse("blue")
            rgba.alpha = 1.0

    return rgba


def rgba_to_rgb_string(rgba: Gdk.RGBA) -> str:
    """Convert Gdk.RGBA to rgb(r,g,b) string format.

    Args:
    ----
        rgba: The RGBA color object.

    Returns:
    -------
        String in the format "rgb(r,g,b)" with integer values 0-255.

    """
    r_int, g_int, b_int = (
        int(rgba.red * 255),
        int(rgba.green * 255),
        int(rgba.blue * 255),
    )
    return f"rgb({r_int},{g_int},{b_int})"


def get_color_scheme(settings: Gio.Settings) -> HeatmapColorScheme:
    """Get the appropriate color scheme based on settings.

    Args:
    ----
        settings: Application settings.

    Returns:
    -------
        HeatmapColorScheme instance.

    """
    use_single_color = settings.get_boolean("use-single-color-heatmap")
    use_accent_color = settings.get_boolean("use-accent-color")

    if use_single_color and use_accent_color:
        return AccentColorHeatmap(settings)
    if use_single_color:
        return SingleColorHeatmap(settings)
    return MultiColorHeatmap(settings)


def get_system_accent_color() -> Gdk.RGBA:
    """Get the system accent color from Adwaita.

    Returns
    -------
        RGBA color object.

    """
    style_manager = Adw.StyleManager.get_default()

    # Default to red for non GNOME desktop
    default_color = Gdk.RGBA()
    default_color.parse("#ff0000")

    if style_manager is not None and style_manager.get_system_supports_accent_colors():
        accent_color = style_manager.get_accent_color()
        try:
            return Adw.accent_color_to_rgba(accent_color)
        except (ValueError, TypeError) as e:
            logger.warning("Failed to convert accent color: %s", e)

    return default_color


class HeatmapColorScheme(ABC):
    """Base class for heatmap coloring systems."""

    # Decide when to use white vs black text
    LUMINANCE_THRESHOLD: Final[float] = 0.5

    def __init__(self: "HeatmapColorScheme", settings: Gio.Settings) -> None:
        """Initialize with settings.

        Args:
        ----
            settings: Application settings.

        """
        self.settings = settings

    @abstractmethod
    def get_color_gradient(
        self: "HeatmapColorScheme",
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get the begin and end color for the gradient.

        Returns
        -------
            A tuple containing:
                - begin_color: RGB tuple (float values 0-1)
                - end_color: RGB tuple (float values 0-1)

        """

    @final
    def calculate_color_for_key(
        self: "HeatmapColorScheme",
        normalized_count: float,
    ) -> tuple[str, str]:
        """Calculate heatmap color and contrast text color based on normalized count.

        Args:
        ----
            normalized_count: A float between 0.0 and 1.0.

        Returns:
        -------
            A tuple containing:
                - str: The calculated background color.
                - str: The calculated text color ('white' or 'black') for contrast.

        """
        beg_color, end_color = self.get_color_gradient()

        r = beg_color[0] + normalized_count * (end_color[0] - beg_color[0])
        g = beg_color[1] + normalized_count * (end_color[1] - beg_color[1])
        b = beg_color[2] + normalized_count * (end_color[2] - beg_color[2])

        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)

        bg_color = f"rgb({r_int}, {g_int}, {b_int})"
        luminance = 0.3 * r + 0.6 * g + 0.1 * b  # Luminance formula provides brightness
        text_color = "white" if luminance < self.LUMINANCE_THRESHOLD else "black"

        return bg_color, text_color

    @final
    def get_gradient_css(self: "HeatmapColorScheme") -> str:
        """Generate CSS for a gradient bar.

        Returns
        -------
            CSS string for gradient bar.

        """
        beg_color, end_color = self.get_color_gradient()

        beg_r, beg_g, beg_b = (int(x * 255) for x in beg_color)
        end_r, end_g, end_b = (int(x * 255) for x in end_color)

        return f"""
        .gradient-bar {{
            background: linear-gradient(to right,
                rgb({beg_r}, {beg_g}, {beg_b}),
                rgb({end_r}, {end_g}, {end_b}));
        }}
        """


class SingleColorHeatmap(HeatmapColorScheme):
    """Single color heatmap with auto-generated light/dark gradient."""

    def _generate_gradient_from_color(
        self: "SingleColorHeatmap",
        color_rgba: Gdk.RGBA,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Generate a gradient pair from a single color.

        Args:
        ----
            color_rgba: The base color to generate gradient from.

        Returns:
        -------
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        r, g, b = color_rgba.red, color_rgba.green, color_rgba.blue
        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        # Lighter version
        light_s = max(0.2, s * 0.6)
        light_v = min(1.0, v * 1.5)
        beg_r, beg_g, beg_b = colorsys.hsv_to_rgb(h, light_s, light_v)
        beg_color = (beg_r, beg_g, beg_b)

        # Darker version
        dark_s = min(1.0, s * 1.5)
        dark_v = max(0.15, v * 0.45)
        end_r, end_g, end_b = colorsys.hsv_to_rgb(h, dark_s, dark_v)
        end_color = (end_r, end_g, end_b)

        if self.settings.get_boolean("reverse-heatmap-gradient"):
            return end_color, beg_color
        return beg_color, end_color

    @override
    def get_color_gradient(
        self: "SingleColorHeatmap",
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get begin and end colors derived from a single color.

        Returns
        -------
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        beg_rgba = parse_color_string(self.settings.get_string("heatmap-single-color"))
        return self._generate_gradient_from_color(beg_rgba)


class AccentColorHeatmap(SingleColorHeatmap):
    """Heatmap using system accent color."""

    @override
    def get_color_gradient(
        self: "AccentColorHeatmap",
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get begin and end colors derived from the system accent color.

        Returns
        -------
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        accent_rgba = get_system_accent_color()

        return self._generate_gradient_from_color(accent_rgba)


class MultiColorHeatmap(HeatmapColorScheme):
    """Multi-color heatmap with user-defined begin and end colors."""

    @override
    def get_color_gradient(
        self: "MultiColorHeatmap",
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get begin and end colors from settings.

        Returns
        -------
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        beg_rgba = parse_color_string(self.settings.get_string("heatmap-begin-color"))
        end_rgba = parse_color_string(self.settings.get_string("heatmap-end-color"))

        beg_color = (beg_rgba.red, beg_rgba.green, beg_rgba.blue)
        end_color = (end_rgba.red, end_rgba.green, end_rgba.blue)

        if self.settings.get_boolean("reverse-heatmap-gradient"):
            return end_color, beg_color
        return beg_color, end_color