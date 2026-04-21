"""Manual per-face color input helpers."""

from .color_state import PRIMARY_COLOR_TO_FACE, normalize_color_tokens, tokenize_color_string


FACE_ORDER = "URFDLB"
FACE_ROTATION_PRESETS = {
    "capture-v1": {
        "U": "counter-clockwise",
        "R": "none",
        "F": "none",
        "D": "none",
        "L": "counter-clockwise",
        "B": "180",
    }
}
VALID_ROTATIONS = {"none", "clockwise", "counter-clockwise", "180"}


class FaceInputError(ValueError):
    """Raised when per-face input is invalid."""


def parse_face_tokens(face_name: str, face_value: str) -> list[str]:
    """Parse one 3x3 face into normalized primary color names."""
    try:
        return normalize_color_tokens(
            tokenize_color_string(face_value),
            expected_count=9,
            input_name=f"{face_name} face input",
        )
    except ValueError as exc:
        raise FaceInputError(str(exc)) from exc


def rotate_face_tokens(tokens: list[str], rotation: str) -> list[str]:
    """Rotate one 3x3 face in row-major order."""
    if len(tokens) != 9:
        raise FaceInputError("Face rotation requires exactly 9 tokens.")
    if rotation not in VALID_ROTATIONS:
        raise FaceInputError(f"Unsupported face rotation: {rotation}.")

    index_map = {
        "none": [0, 1, 2, 3, 4, 5, 6, 7, 8],
        "clockwise": [6, 3, 0, 7, 4, 1, 8, 5, 2],
        "counter-clockwise": [2, 5, 8, 1, 4, 7, 0, 3, 6],
        "180": [8, 7, 6, 5, 4, 3, 2, 1, 0],
    }[rotation]
    return [tokens[index] for index in index_map]


def assemble_faces(
    face_inputs: dict[str, str],
    *,
    orientation_preset: str = "capture-v1",
) -> list[str]:
    """Parse, rotate, and assemble per-face inputs in Kociemba face order."""
    if orientation_preset not in FACE_ROTATION_PRESETS:
        raise FaceInputError(f"Unsupported face orientation preset: {orientation_preset}.")

    preset = FACE_ROTATION_PRESETS[orientation_preset]
    if missing_faces := [
        face for face in FACE_ORDER if face not in face_inputs
    ]:
        joined = ", ".join(missing_faces)
        raise FaceInputError(f"Missing face inputs: {joined}.")

    assembled: list[str] = []
    for face in FACE_ORDER:
        parsed_tokens = parse_face_tokens(face, face_inputs[face])
        rotated_tokens = rotate_face_tokens(parsed_tokens, preset[face])
        assembled.extend(rotated_tokens)

    return assembled


def assemble_faces_to_color_string(
    face_inputs: dict[str, str],
    *,
    orientation_preset: str = "capture-v1",
) -> str:
    """Assemble per-face inputs into one Kociemba-ordered color string."""
    return " ".join(assemble_faces(face_inputs, orientation_preset=orientation_preset))


def assemble_faces_to_facelet_string(
    face_inputs: dict[str, str],
    *,
    orientation_preset: str = "capture-v1",
) -> str:
    """Assemble per-face inputs directly into a Kociemba facelet string."""
    assembled_colors = assemble_faces(face_inputs, orientation_preset=orientation_preset)
    return "".join(PRIMARY_COLOR_TO_FACE[color] for color in assembled_colors)
