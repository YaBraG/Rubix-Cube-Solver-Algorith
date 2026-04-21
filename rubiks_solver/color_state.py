"""Color-name cube state conversion helpers."""

from collections import Counter

from .validation import EXPECTED_LENGTH


DEFAULT_COLOR_TO_FACE_MAPPING = {
    "white": "U",
    "yellow": "D",
    "green": "F",
    "blue": "B",
    "red": "R",
    "orange": "L",
}


class ColorStateError(ValueError):
    """Raised when color-name cube state input is invalid."""


def colors_to_facelet_string(
    colors: str, color_to_face_mapping: dict[str, str] | None = None
) -> str:
    """Convert 54 color names into a Kociemba facelet string."""
    mapping = color_to_face_mapping or DEFAULT_COLOR_TO_FACE_MAPPING
    normalized_colors = [color.strip().lower() for color in colors.split() if color.strip()]

    if len(normalized_colors) != EXPECTED_LENGTH:
        raise ColorStateError(f"Color input must contain {EXPECTED_LENGTH} colors.")

    unknown_colors = sorted(set(normalized_colors) - set(mapping))
    if unknown_colors:
        joined = ", ".join(unknown_colors)
        raise ColorStateError(f"Color input contains unknown colors: {joined}.")

    counts = Counter(normalized_colors)
    if any(counts.get(color, 0) != 9 for color in mapping):
        parts = [
            f"{color}={counts.get(color, 0)}"
            for color in mapping
            if counts.get(color, 0) != 9
        ]
        detail = ", ".join(parts)
        raise ColorStateError(f"Color input has wrong color counts: {detail}.")

    return "".join(mapping[color] for color in normalized_colors)
