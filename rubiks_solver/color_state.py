"""Color-name cube state conversion helpers."""

from collections import Counter

from .validation import EXPECTED_LENGTH


DEFAULT_COLOR_TO_FACE_MAPPING = {
    "white": "U",
    "w": "U",
    "yellow": "D",
    "y": "D",
    "green": "F",
    "g": "F",
    "blue": "B",
    "b": "B",
    "red": "R",
    "r": "R",
    "orange": "L",
    "o": "L",
}

DEFAULT_FACE_TO_PRIMARY_COLOR = {
    "U": "white",
    "D": "yellow",
    "F": "green",
    "B": "blue",
    "R": "red",
    "L": "orange",
}

ACCEPTED_COLOR_TOKENS = "white/w, yellow/y, green/g, blue/b, red/r, orange/o"


class ColorStateError(ValueError):
    """Raised when color-name cube state input is invalid."""


def colors_to_facelet_string(
    colors: str, color_to_face_mapping: dict[str, str] | None = None
) -> str:
    """Convert 54 color tokens into a Kociemba facelet string."""
    mapping = color_to_face_mapping or DEFAULT_COLOR_TO_FACE_MAPPING
    normalized_colors = [color.strip().lower() for color in colors.split() if color.strip()]

    if len(normalized_colors) != EXPECTED_LENGTH:
        raise ColorStateError(
            f"Color input must contain {EXPECTED_LENGTH} color tokens. "
            f"Accepted tokens: {ACCEPTED_COLOR_TOKENS}."
        )

    unknown_colors = sorted(set(normalized_colors) - set(mapping))
    if unknown_colors:
        joined = ", ".join(unknown_colors)
        raise ColorStateError(
            f"Color input contains unknown tokens: {joined}. "
            f"Accepted tokens: {ACCEPTED_COLOR_TOKENS}."
        )

    normalized_primary_colors = [
        DEFAULT_FACE_TO_PRIMARY_COLOR[mapping[color]] for color in normalized_colors
    ]

    counts = Counter(normalized_primary_colors)
    if any(counts.get(color, 0) != 9 for color in DEFAULT_FACE_TO_PRIMARY_COLOR.values()):
        parts = [
            f"{color}={counts.get(color, 0)}"
            for color in DEFAULT_FACE_TO_PRIMARY_COLOR.values()
            if counts.get(color, 0) != 9
        ]
        detail = ", ".join(parts)
        raise ColorStateError(
            f"Color input has wrong color counts: {detail}. "
            f"Accepted tokens: {ACCEPTED_COLOR_TOKENS}."
        )

    return "".join(mapping[color] for color in normalized_colors)
