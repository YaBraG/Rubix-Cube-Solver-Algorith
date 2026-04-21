"""Cube solving logic backed by kociemba."""

import kociemba

from .validation import CubeValidationError, validate_cube_state

SOLVED_CUBE_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


class CubeSolveError(RuntimeError):
    """Raised when solver cannot solve provided cube state."""


def solve_cube(cube_state: str) -> str:
    """Validate and solve a Rubik's Cube facelet string."""
    normalized = validate_cube_state(cube_state)

    if normalized == SOLVED_CUBE_STATE:
        return ""

    try:
        return kociemba.solve(normalized)
    except ValueError as exc:
        raise CubeSolveError("Cube state is impossible to solve.") from exc
    except Exception as exc:  # pragma: no cover
        raise CubeSolveError("Solver failed unexpectedly.") from exc
