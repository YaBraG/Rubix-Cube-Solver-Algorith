"""CLI entry point for manual cube-state solving."""

import argparse
import sys

from .color_state import ColorStateError, colors_to_facelet_string
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
            "Solve a Rubik's Cube from either a 54-character Kociemba facelet "
            "string or 54 color names, then print both standard moves and "
            "robot-friendly commands."
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
    parser.add_argument(
        "--colors",
        help=(
            "54 space-separated sticker colors in Kociemba face order "
            "(Up, Right, Front, Down, Left, Back)."
        ),
    )
    return parser


def format_robot_commands(commands: list[tuple[str, int]]) -> str:
    if not commands:
        return "Cube already solved. No robot moves needed."

    return "\n".join(f"{color}, {angle}" for color, angle in commands)


def resolve_cube_state_input(
    cube_state: str | None,
    colors: str | None,
    parser: argparse.ArgumentParser,
) -> str | None:
    if cube_state and colors:
        parser.error("Provide either a facelet cube state or --colors, not both.")

    if colors:
        return colors_to_facelet_string(colors)

    return cube_state


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cube_state = resolve_cube_state_input(args.cube_state, args.colors, parser)
        if not cube_state:
            parser.print_help()
            return 1

        solution = solve_cube(cube_state)
        robot_commands = convert_solution_to_robot_commands(
            solution,
            DEFAULT_FACE_COLOR_MAPPING,
        )
    except ColorStateError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except CubeValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except CubeSolveError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    print("Solution:")
    print(solution or "Cube already solved.")
    print()
    print("Robot commands:")
    print(format_robot_commands(robot_commands))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
