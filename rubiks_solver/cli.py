"""CLI entry point for manual cube-state solving."""

import argparse
import sys

from .robot_moves import (
    DEFAULT_FACE_COLOR_MAPPING,
    convert_solution_to_robot_commands,
)
from .solver import CubeSolveError, solve_cube
from .validation import CubeValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-solver",
        description=(
            "Solve a Rubik's Cube from a 54-character Kociemba facelet string "
            "and print both standard moves and robot-friendly commands."
        ),
    )
    parser.add_argument(
        "cube_state",
        nargs="?",
        help=(
            "54-character cube state in Kociemba order: "
            "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
        ),
    )
    return parser


def format_robot_commands(commands: list[tuple[str, int]]) -> str:
    if not commands:
        return "Cube already solved. No robot moves needed."

    return "\n".join(f"{color}, {angle}" for color, angle in commands)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.cube_state:
        parser.print_help()
        return 1

    try:
        solution = solve_cube(args.cube_state)
        robot_commands = convert_solution_to_robot_commands(
            solution,
            DEFAULT_FACE_COLOR_MAPPING,
        )
    except CubeValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except CubeSolveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    print("Solution:")
    print(solution if solution else "Cube already solved.")
    print()
    print("Robot commands:")
    print(format_robot_commands(robot_commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
