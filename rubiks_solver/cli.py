"""CLI entry point for manual cube-state solving."""

import argparse
import sys

from .color_state import ColorStateError, colors_to_facelet_string
from .face_input import FACE_ORDER, FaceInputError, assemble_faces_to_facelet_string
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
            "string or 54 color tokens, then print both standard moves and "
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
        "--faces",
        action="store_true",
        help="Read six faces separately for manual picture-assisted input.",
    )
    parser.add_argument(
        "--colors",
        help=(
            "54 space-separated sticker color tokens in Kociemba face order "
            "(Up, Right, Front, Down, Left, Back). Use white/w, yellow/y, "
            "green/g, blue/b, red/r, orange/o."
        ),
    )
    for face in FACE_ORDER:
        parser.add_argument(
            f"--{face.lower()}",
            dest=face.lower(),
            help=f"9 space-separated color tokens for {face} face input.",
        )
    parser.add_argument(
        "--face-orientation",
        default="capture-v1",
        choices=["capture-v1"],
        help="Face orientation preset for --faces mode. Default: capture-v1.",
    )
    return parser


def format_robot_commands(commands: list[tuple[str, int]]) -> str:
    if not commands:
        return "Cube already solved. No robot moves needed."

    return "\n".join(f"{color}, {angle}" for color, angle in commands)


def resolve_cube_state_input(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> str | None:
    face_values = {face: getattr(args, face.lower()) for face in FACE_ORDER}
    provided_face_args = [face for face, value in face_values.items() if value]

    if args.faces and args.cube_state:
        parser.error("Provide either a facelet cube state or --faces, not both.")
    if args.faces and args.colors:
        parser.error("Provide either --colors or --faces, not both.")
    if args.cube_state and args.colors:
        parser.error("Provide either a facelet cube state or --colors, not both.")
    if provided_face_args and not args.faces:
        parser.error("Face arguments require --faces.")

    if args.faces:
        missing_faces = [face for face in FACE_ORDER if not face_values[face]]
        if missing_faces:
            joined = ", ".join(f"--{face.lower()}" for face in missing_faces)
            parser.error(f"--faces requires all six face arguments. Missing: {joined}.")
        return assemble_faces_to_facelet_string(
            {face: face_values[face] for face in FACE_ORDER},
            orientation_preset=args.face_orientation,
        )

    if args.colors:
        return colors_to_facelet_string(args.colors)

    return args.cube_state


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cube_state = resolve_cube_state_input(args, parser)
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
    except FaceInputError as exc:
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
