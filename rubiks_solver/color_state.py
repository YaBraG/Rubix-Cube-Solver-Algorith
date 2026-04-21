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

PRIMARY_COLOR_TO_FACE = {
    color: face for face, color in DEFAULT_FACE_TO_PRIMARY_COLOR.items()
}

ACCEPTED_COLOR_TOKENS = "white/w, yellow/y, green/g, blue/b, red/r, orange/o"


class ColorStateError(ValueError):
    """Raised when color-name cube state input is invalid."""


def tokenize_color_string(colors: str) -> list[str]:
    """Split color input into normalized raw tokens."""
    return [color.strip().lower() for color in colors.split() if color.strip()]


def normalize_color_tokens(
    tokens: list[str],
    *,
    expected_count: int,
    input_name: str,
    color_to_face_mapping: dict[str, str] | None = None,
) -> list[str]:
    """Validate raw color tokens and normalize them into primary color names."""
    mapping = color_to_face_mapping or DEFAULT_COLOR_TO_FACE_MAPPING

    if len(tokens) != expected_count:
        raise ColorStateError(
            f"{input_name} must contain {expected_count} color tokens. "
            f"Accepted tokens: {ACCEPTED_COLOR_TOKENS}."
        )

    if unknown_colors := sorted(set(tokens) - set(mapping)):
        joined = ", ".join(unknown_colors)
        raise ColorStateError(
            f"{input_name} contains unknown tokens: {joined}. "
            f"Accepted tokens: {ACCEPTED_COLOR_TOKENS}."
        )

    return [DEFAULT_FACE_TO_PRIMARY_COLOR[mapping[color]] for color in tokens]


def colors_to_facelet_string(
    colors: str, color_to_face_mapping: dict[str, str] | None = None
) -> str:
    """Convert 54 color tokens into a Kociemba facelet string."""
    normalized_primary_colors = normalize_color_tokens(
        tokenize_color_string(colors),
        expected_count=EXPECTED_LENGTH,
        input_name="Color input",
        color_to_face_mapping=color_to_face_mapping,
    )

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

    return "".join(PRIMARY_COLOR_TO_FACE[color] for color in normalized_primary_colors)
