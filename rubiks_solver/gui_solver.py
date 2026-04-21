"""GUI-facing solving helpers shared by manual and camera-review screens."""

from __future__ import annotations

from typing import Any

from .color_state import PRIMARY_COLOR_TO_FACE
from .gui_models import editor_faces_to_color_lists, summarize_editor_state, unknown_positions
from .live_face_scanner import DEFAULT_FACE_SEQUENCE
from .robot_moves import convert_solution_to_robot_commands
from .solver import CubeSolveError, solve_cube


def build_facelet_string_from_editor(faces: dict[str, list[str]]) -> str:
    normalized = editor_faces_to_color_lists(faces)
    return "".join(
        PRIMARY_COLOR_TO_FACE[color]
        for face in DEFAULT_FACE_SEQUENCE
        for color in normalized[face]
    )


def build_result_payload(
    *,
    faces: dict[str, list[str]],
    solution: str | None,
    commands: list[tuple[str, int]],
    error: str | None = None,
) -> dict[str, Any]:
    summary = summarize_editor_state(faces)
    return {
        "success": error is None,
        "error": error,
        "faces": summary["faces"],
        "rows": summary["rows"],
        "color_counts": summary["color_counts"],
        "unknown_positions": summary["unknown_positions"],
        "solution": solution,
        "commands": [{"color": color, "angle": angle} for color, angle in commands],
        "move_count": len(solution.split()) if solution else 0,
    }


def solve_editor_faces(faces: dict[str, list[str]]) -> dict[str, Any]:
    unknowns = unknown_positions(faces)
    if unknowns:
        return build_result_payload(
            faces=faces,
            solution=None,
            commands=[],
            error=f"Unknown stickers remain: {', '.join(unknowns)}.",
        )

    try:
        facelet_string = build_facelet_string_from_editor(faces)
    except KeyError as exc:
        bad_color = str(exc).strip("'")
        return build_result_payload(
            faces=faces,
            solution=None,
            commands=[],
            error=f"Invalid sticker color in editor state: {bad_color}.",
        )

    try:
        solution = solve_cube(facelet_string)
    except CubeSolveError as exc:
        return build_result_payload(
            faces=faces,
            solution=None,
            commands=[],
            error=str(exc),
        )

    commands = convert_solution_to_robot_commands(solution)
    return build_result_payload(
        faces=faces,
        solution=solution or "",
        commands=commands,
    )
