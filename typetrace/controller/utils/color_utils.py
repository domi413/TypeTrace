"""Utility functions for color manipulation."""

from gi.repository import Gdk


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
