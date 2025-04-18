"""Utility functions for color manipulation."""

from __future__ import annotations

import colorsys
from abc import ABC, abstractmethod
from typing import Final, override

from gi.repository import Gdk, Gio


def parse_color_string(color_str: str) -> Gdk.RGBA:
    """Parse a color string into a Gdk.RGBA object.

    Handles formats like "rgb(r,g,b)" and standard Gdk color names/formats.

    Args:
        color_str: String representation of a color (e.g., "rgb(0,0,255)").

    Returns:
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


def get_color_scheme(settings: Gio.Settings) -> HeatmapColorScheme:
    """Get the appropriate color scheme based on settings.

    Args:
        settings: Application settings.

    Returns:
        HeatmapColorScheme instance.

    """
    if settings.get_boolean("use-single-color-heatmap"):
        return SingleColorHeatmap(settings)
    return MultiColorHeatmap(settings)


class HeatmapColorScheme(ABC):
    """Base class for heatmap coloring systems."""

    # Decide when to use white vs black text
    LUMINANCE_THRESHOLD: Final[float] = 0.5

    def __init__(self, settings: Gio.Settings) -> None:
        """Initialize with settings.

        Args:
            settings: Application settings.

        """
        self.settings = settings

    @abstractmethod
    def get_color_gradient(
        self,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get the begin and end color for the gradient.

        Returns:
            A tuple containing:
                - begin_color: RGB tuple (float values 0-1)
                - end_color: RGB tuple (float values 0-1)

        """

    def calculate_color_for_key(
        self,
        normalized_count: float,
    ) -> tuple[str, str]:
        """Calculate heatmap color and contrast text color based on normalized count.

        Args:
            normalized_count: A float between 0.0 and 1.0.

        Returns:
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

    def get_gradient_css(self) -> str:
        """Generate CSS for a gradient bar.

        Returns:
            CSS string for gradient bar.

        """
        beg_color, end_color = self.get_color_gradient()

        beg_r, beg_g, beg_b = [int(x * 255) for x in beg_color]
        end_r, end_g, end_b = [int(x * 255) for x in end_color]

        return f"""
        .gradient-bar {{
            background: linear-gradient(to right,
                rgb({beg_r}, {beg_g}, {beg_b}),
                rgb({end_r}, {end_g}, {end_b}));
        }}
        """


class SingleColorHeatmap(HeatmapColorScheme):
    """Single color heatmap with auto-generated light/dark gradient."""

    @override
    def get_color_gradient(
        self,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get begin and end colors derived from a single color.

        Returns:
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        beg_rgba = parse_color_string(self.settings.get_string("heatmap-begin-color"))
        r, g, b = beg_rgba.red, beg_rgba.green, beg_rgba.blue
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


class MultiColorHeatmap(HeatmapColorScheme):
    """Multi-color heatmap with user-defined begin and end colors."""

    @override
    def get_color_gradient(
        self,
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """Get begin and end colors from settings.

        Returns:
            Tuple of (begin_color, end_color) as RGB tuples.

        """
        beg_rgba = parse_color_string(self.settings.get_string("heatmap-begin-color"))
        end_rgba = parse_color_string(self.settings.get_string("heatmap-end-color"))

        beg_color = (beg_rgba.red, beg_rgba.green, beg_rgba.blue)
        end_color = (end_rgba.red, end_rgba.green, end_rgba.blue)

        if self.settings.get_boolean("reverse-heatmap-gradient"):
            return end_color, beg_color
        return beg_color, end_color
