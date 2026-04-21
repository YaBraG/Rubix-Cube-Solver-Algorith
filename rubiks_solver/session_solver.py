"""Solve a cube from a completed live scan session."""

from __future__ import annotations

import argparse
import json
import shlex
from collections import Counter
from pathlib import Path
from typing import Any

from .color_state import DEFAULT_FACE_TO_PRIMARY_COLOR, PRIMARY_COLOR_TO_FACE
from .live_face_scanner import DEFAULT_FACE_SEQUENCE
from .robot_moves import convert_solution_to_robot_commands
from .solver import CubeSolveError, solve_cube


VALID_COLORS = tuple(DEFAULT_FACE_TO_PRIMARY_COLOR.values())
FACE_FILE_NAMES = {face: f"{face.lower()}_face_scan.json" for face in DEFAULT_FACE_SEQUENCE}


class SessionSolveError(ValueError):
    """Raised when a live scan session cannot be solved."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-session-solver",
        description=(
            "Read a completed live scan session, inject virtual centers, validate colors, "
            "and solve the cube."
        ),
    )
    parser.add_argument("--session-dir", required=True, help="Directory with face scan JSON files.")
    parser.add_argument("--output", help="Optional path to write a solve report JSON.")
    parser.add_argument(
        "--allow-unknown",
        action="store_true",
        help="Keep unknown non-center stickers in the report and skip solving instead of failing early.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Manual color correction like U0=white or F8=blue. Can be repeated.",
    )
    parser.add_argument(
        "--allow-center-override",
        action="store_true",
        help="Let overrides replace virtual centers. Default keeps virtual centers for solving.",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print equivalent python -m rubiks_solver.cli --faces command for debugging.",
    )
    return parser


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SessionSolveError(f"Missing scan file: {path.name}.") from exc
    except json.JSONDecodeError as exc:
        raise SessionSolveError(f"Invalid JSON in scan file: {path.name}.") from exc


def load_session_face(session_dir: Path, face: str) -> dict[str, Any]:
    path = session_dir / FACE_FILE_NAMES[face]
    payload = load_json_file(path)

    if payload.get("face") != face:
        found = payload.get("face")
        raise SessionSolveError(
            f"{path.name} has wrong face label: expected {face}, got {found!r}."
        )

    samples = payload.get("samples")
    if not isinstance(samples, list) or len(samples) != 9:
        raise SessionSolveError(f"{path.name} must contain a samples list with 9 entries.")

    indexes = sorted(sample.get("index") for sample in samples if isinstance(sample, dict))
    if indexes != list(range(9)):
        raise SessionSolveError(f"{path.name} must contain sample indexes 0 through 8 exactly once.")

    for sample in samples:
        if "classified_color" not in sample:
            raise SessionSolveError(
                f"{path.name} sample {sample.get('index')} is missing classified_color."
            )

    return payload


def load_scan_session(session_dir: str | Path) -> dict[str, dict[str, Any]]:
    session_path = Path(session_dir)
    return {face: load_session_face(session_path, face) for face in DEFAULT_FACE_SEQUENCE}


def parse_override(override: str) -> tuple[str, int, str]:
    if "=" not in override:
        raise SessionSolveError(f"Invalid override format: {override}. Use FACEINDEX=color.")

    location, color = override.split("=", 1)
    location = location.strip().upper()
    color = color.strip().lower()

    if len(location) != 2 or location[0] not in DEFAULT_FACE_SEQUENCE or not location[1].isdigit():
        raise SessionSolveError(f"Invalid override target: {override}. Use FACEINDEX=color.")

    index = int(location[1])
    if not 0 <= index <= 8:
        raise SessionSolveError(f"Invalid override index in {override}. Index must be 0 through 8.")

    if color not in VALID_COLORS:
        joined = ", ".join(VALID_COLORS)
        raise SessionSolveError(f"Invalid override color in {override}. Use one of: {joined}.")

    return location[0], index, color


def parse_overrides(overrides: list[str]) -> list[dict[str, Any]]:
    return [
        {"face": face, "index": index, "color": color}
        for face, index, color in (parse_override(override) for override in overrides)
    ]


def extract_session_faces(
    session_payloads: dict[str, dict[str, Any]],
    *,
    overrides: list[dict[str, Any]] | None = None,
    allow_center_override: bool = False,
) -> tuple[dict[str, list[str]], list[str]]:
    faces: dict[str, list[str]] = {}
    virtual_center_notes: list[str] = []

    for face in DEFAULT_FACE_SEQUENCE:
        samples = sorted(session_payloads[face]["samples"], key=lambda sample: sample["index"])
        colors = [str(sample["classified_color"]).lower() for sample in samples]
        virtual_center = DEFAULT_FACE_TO_PRIMARY_COLOR[face]
        colors[4] = virtual_center
        faces[face] = colors
        virtual_center_notes.append(f"{face}4={virtual_center}")

    for override in overrides or []:
        if override["index"] == 4 and not allow_center_override:
            continue
        faces[override["face"]][override["index"]] = override["color"]

    return faces, virtual_center_notes


def collect_unknown_stickers(faces: dict[str, list[str]]) -> list[str]:
    unknowns: list[str] = []
    for face in DEFAULT_FACE_SEQUENCE:
        for index, color in enumerate(faces[face]):
            if color == "unknown":
                unknowns.append(f"{face}{index}")
    return unknowns


def count_colors(faces: dict[str, list[str]]) -> dict[str, int]:
    counts = Counter()
    for face in DEFAULT_FACE_SEQUENCE:
        counts.update(faces[face])
    return {color: counts.get(color, 0) for color in VALID_COLORS}


def summarize_count_errors(color_counts: dict[str, int]) -> dict[str, list[str]]:
    over = [f"{color}={count}" for color, count in color_counts.items() if count > 9]
    under = [f"{color}={count}" for color, count in color_counts.items() if count < 9]
    return {"over": over, "under": under}


def format_face_rows(faces: dict[str, list[str]]) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for face in DEFAULT_FACE_SEQUENCE:
        colors = faces[face]
        rows[face] = [
            " ".join(color[0] if color != "orange" else "o" for color in colors[0:3]),
            " ".join(color[0] if color != "orange" else "o" for color in colors[3:6]),
            " ".join(color[0] if color != "orange" else "o" for color in colors[6:9]),
        ]
    return rows


def build_facelet_string(faces: dict[str, list[str]]) -> str:
    return "".join(PRIMARY_COLOR_TO_FACE[color] for face in DEFAULT_FACE_SEQUENCE for color in faces[face])


def build_debug_faces_command(faces: dict[str, list[str]]) -> str:
    face_flags = []
    for face in DEFAULT_FACE_SEQUENCE:
        values = " ".join(color[0] if color != "orange" else "o" for color in faces[face])
        face_flags.append(f"--{face.lower()} {shlex.quote(values)}")
    return "python -m rubiks_solver.cli --faces " + " ".join(face_flags)


def build_report_payload(
    *,
    session_dir: str | Path,
    faces: dict[str, list[str]],
    facelet_string: str | None,
    color_counts: dict[str, int],
    virtual_center_notes: list[str],
    overrides_applied: list[dict[str, Any]],
    solution: str | None,
    commands: list[dict[str, Any]],
    error: str | None = None,
    unknown_stickers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "session_dir": str(session_dir),
        "faces": faces,
        "shorthand_rows": format_face_rows(faces),
        "color_counts": color_counts,
        "virtual_centers_used": True,
        "virtual_center_replacements": virtual_center_notes,
        "overrides_applied": overrides_applied,
        "facelet_string": facelet_string,
        "solution": solution,
        "commands": commands,
        "unknown_stickers": unknown_stickers or [],
        "error": error,
    }


def write_report(path: str | Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def print_face_rows(faces: dict[str, list[str]]) -> None:
    rows = format_face_rows(faces)
    for face in DEFAULT_FACE_SEQUENCE:
        print(f"{face} face:")
        for row in rows[face]:
            print(row)
        print()


def print_color_counts(color_counts: dict[str, int]) -> None:
    print("Color counts:")
    for color in VALID_COLORS:
        print(f"  {color}: {color_counts[color]}")


def convert_commands_for_report(solution: str | None) -> list[dict[str, Any]]:
    if solution is None:
        return []
    return [
        {"color": color, "angle": angle}
        for color, angle in convert_solution_to_robot_commands(solution)
    ]


def solve_session(
    *,
    session_dir: str | Path,
    allow_unknown: bool = False,
    override_strings: list[str] | None = None,
    allow_center_override: bool = False,
    output: str | None = None,
    print_command: bool = False,
) -> tuple[int, dict[str, Any]]:
    try:
        payloads = load_scan_session(session_dir)
        overrides_applied = parse_overrides(override_strings or [])
        faces, virtual_center_notes = extract_session_faces(
            payloads,
            overrides=overrides_applied,
            allow_center_override=allow_center_override,
        )
    except SessionSolveError as exc:
        report = {
            "session_dir": str(session_dir),
            "virtual_centers_used": True,
            "error": str(exc),
        }
        if output:
            write_report(output, report)
        print(f"Error: {exc}")
        return 2, report

    print_face_rows(faces)
    print("Virtual center replacements applied:")
    print("  " + ", ".join(virtual_center_notes))

    color_counts = count_colors(faces)
    print_color_counts(color_counts)

    if print_command:
        print("Equivalent --faces command:")
        print(build_debug_faces_command(faces))

    unknown_stickers = collect_unknown_stickers(faces)
    if unknown_stickers:
        message = f"Unknown sticker colors at: {', '.join(unknown_stickers)}."
        if allow_unknown:
            message += " Solving skipped because unknown colors remain."
        report = build_report_payload(
            session_dir=session_dir,
            faces=faces,
            facelet_string=None,
            color_counts=color_counts,
            virtual_center_notes=virtual_center_notes,
            overrides_applied=overrides_applied,
            solution=None,
            commands=[],
            error=message,
            unknown_stickers=unknown_stickers,
        )
        if output:
            write_report(output, report)
        print(f"Error: {message}")
        return 2, report

    count_errors = summarize_count_errors(color_counts)
    if count_errors["over"] or count_errors["under"]:
        detail_parts = []
        if count_errors["over"]:
            detail_parts.append("over: " + ", ".join(count_errors["over"]))
        if count_errors["under"]:
            detail_parts.append("under: " + ", ".join(count_errors["under"]))
        message = "Color counts are invalid: " + " | ".join(detail_parts)
        report = build_report_payload(
            session_dir=session_dir,
            faces=faces,
            facelet_string=None,
            color_counts=color_counts,
            virtual_center_notes=virtual_center_notes,
            overrides_applied=overrides_applied,
            solution=None,
            commands=[],
            error=message,
        )
        if output:
            write_report(output, report)
        print(f"Error: {message}")
        return 2, report

    facelet_string = build_facelet_string(faces)
    try:
        solution = solve_cube(facelet_string)
    except CubeSolveError as exc:
        report = build_report_payload(
            session_dir=session_dir,
            faces=faces,
            facelet_string=facelet_string,
            color_counts=color_counts,
            virtual_center_notes=virtual_center_notes,
            overrides_applied=overrides_applied,
            solution=None,
            commands=[],
            error=str(exc),
        )
        if output:
            write_report(output, report)
        print(f"Error: {exc}")
        return 2, report

    commands = convert_commands_for_report(solution)
    report = build_report_payload(
        session_dir=session_dir,
        faces=faces,
        facelet_string=facelet_string,
        color_counts=color_counts,
        virtual_center_notes=virtual_center_notes,
        overrides_applied=overrides_applied,
        solution=solution,
        commands=commands,
    )

    if solution:
        print("Solution:")
        print(solution)
        print("Robot commands:")
        for command in commands:
            print(f"{command['color']}, {command['angle']}")
    else:
        print("Cube already solved.")
        print("No robot moves needed.")

    if output:
        write_report(output, report)

    return 0, report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    exit_code, _report = solve_session(
        session_dir=args.session_dir,
        allow_unknown=args.allow_unknown,
        override_strings=args.override,
        allow_center_override=args.allow_center_override,
        output=args.output,
        print_command=args.print_command,
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
