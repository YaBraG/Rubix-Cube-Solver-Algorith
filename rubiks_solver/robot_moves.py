"""Convert Rubik's notation into robot-friendly commands."""

DEFAULT_FACE_COLOR_MAPPING = {
    "U": "white",
    "D": "yellow",
    "R": "red",
    "L": "orange",
    "F": "green",
    "B": "blue",
}


def convert_move_to_robot_command(
    move: str, face_color_mapping: dict[str, str] | None = None
) -> tuple[str, int]:
    """Convert one Rubik's move into a color and angle pair."""
    mapping = face_color_mapping or DEFAULT_FACE_COLOR_MAPPING
    normalized = move.strip().upper()

    if not normalized:
        raise ValueError("Move cannot be empty.")

    face = normalized[0]
    if face not in mapping:
        raise ValueError(f"Unsupported face move: {move}.")

    suffix = normalized[1:]
    if suffix == "":
        angle = 90
    elif suffix == "'":
        angle = -90
    elif suffix == "2":
        angle = 180
    else:
        raise ValueError(f"Unsupported move format: {move}.")

    return mapping[face], angle


def convert_solution_to_robot_commands(
    solution: str, face_color_mapping: dict[str, str] | None = None
) -> list[tuple[str, int]]:
    """Convert full Rubik's notation solution string into robot commands."""
    normalized = solution.strip()
    if not normalized:
        return []

    return [
        convert_move_to_robot_command(move, face_color_mapping)
        for move in normalized.split()
    ]
