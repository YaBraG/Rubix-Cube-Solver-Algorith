import json

import pytest

from rubiks_solver.session_solver import (
    build_parser,
    extract_session_faces,
    load_scan_session,
    parse_override,
    solve_session,
)


SOLVED_FACE_COLORS = {
    "U": ["white"] * 9,
    "R": ["red"] * 9,
    "F": ["green"] * 9,
    "D": ["yellow"] * 9,
    "L": ["orange"] * 9,
    "B": ["blue"] * 9,
}


def write_face_scan(session_dir, face, colors):
    samples = [
        {
            "index": index,
            "classified_color": color,
        }
        for index, color in enumerate(colors)
    ]
    payload = {"face": face, "samples": samples}
    path = session_dir / f"{face.lower()}_face_scan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_solved_session(session_dir):
    session_dir.mkdir(parents=True, exist_ok=True)
    for face, colors in SOLVED_FACE_COLORS.items():
        write_face_scan(session_dir, face, colors)


def test_loading_complete_valid_session(tmp_path):
    write_solved_session(tmp_path)

    payloads = load_scan_session(tmp_path)

    assert set(payloads) == {"U", "R", "F", "D", "L", "B"}
    assert payloads["U"]["face"] == "U"


def test_virtual_centers_replace_index_4(tmp_path):
    write_solved_session(tmp_path)
    bad_center_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_center_payload["samples"][4]["classified_color"] = "blue"
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_center_payload), encoding="utf-8")

    payloads = load_scan_session(tmp_path)
    faces, notes = extract_session_faces(payloads)

    assert faces["U"][4] == "white"
    assert "U4=white" in notes


def test_missing_file_error(tmp_path, capsys):
    write_solved_session(tmp_path)
    (tmp_path / "b_face_scan.json").unlink()

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 2
    assert "Missing scan file" in report["error"]
    assert "Missing scan file" in capsys.readouterr().out


def test_wrong_face_label_error(tmp_path):
    write_solved_session(tmp_path)
    bad_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_payload["face"] = "R"
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_payload), encoding="utf-8")

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 2
    assert "wrong face label" in report["error"]


def test_wrong_sample_count_error(tmp_path):
    write_solved_session(tmp_path)
    bad_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_payload["samples"] = bad_payload["samples"][:8]
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_payload), encoding="utf-8")

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 2
    assert "9 entries" in report["error"]


def test_unknown_non_center_color_fails_by_default(tmp_path):
    write_solved_session(tmp_path)
    bad_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_payload["samples"][0]["classified_color"] = "unknown"
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_payload), encoding="utf-8")

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 2
    assert report["unknown_stickers"] == ["U0"]


def test_override_fixes_wrong_color(tmp_path):
    write_solved_session(tmp_path)
    bad_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_payload["samples"][0]["classified_color"] = "red"
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_payload), encoding="utf-8")

    exit_code, report = solve_session(session_dir=tmp_path, override_strings=["U0=white"])

    assert exit_code == 0
    assert report["faces"]["U"][0] == "white"


def test_invalid_override_rejected(tmp_path):
    write_solved_session(tmp_path)

    exit_code, report = solve_session(session_dir=tmp_path, override_strings=["U9=white"])

    assert exit_code == 2
    assert "Invalid override index" in report["error"]


def test_color_counts_validation(tmp_path):
    write_solved_session(tmp_path)
    bad_payload = json.loads((tmp_path / "u_face_scan.json").read_text(encoding="utf-8"))
    bad_payload["samples"][0]["classified_color"] = "red"
    (tmp_path / "u_face_scan.json").write_text(json.dumps(bad_payload), encoding="utf-8")

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 2
    assert "Color counts are invalid" in report["error"]
    assert report["color_counts"]["white"] == 8
    assert report["color_counts"]["red"] == 10


def test_solving_solved_cube_session(tmp_path, capsys):
    write_solved_session(tmp_path)

    exit_code, report = solve_session(session_dir=tmp_path)

    assert exit_code == 0
    assert report["solution"] == ""
    captured = capsys.readouterr()
    assert "Cube already solved." in captured.out


def test_output_report_contains_solution_and_commands(tmp_path):
    write_solved_session(tmp_path)
    output = tmp_path / "solve_report.json"

    exit_code, report = solve_session(session_dir=tmp_path, output=str(output))

    assert exit_code == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["solution"] == ""
    assert saved["commands"] == []
    assert saved["virtual_centers_used"] is True
    assert report["facelet_string"] == "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_print_command_formatting(tmp_path, capsys):
    write_solved_session(tmp_path)

    exit_code, _report = solve_session(session_dir=tmp_path, print_command=True)

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "python -m rubiks_solver.cli --faces" in captured.out
    assert '--u "w w w w w w w w w"' in captured.out or "--u 'w w w w w w w w w'" in captured.out


def test_parser_help_accepts_allow_unknown_and_override():
    parser = build_parser()

    args = parser.parse_args(
        ["--session-dir", "captures/session_1", "--allow-unknown", "--override", "U0=white"]
    )

    assert args.allow_unknown is True
    assert args.override == ["U0=white"]


def test_parse_override():
    assert parse_override("F8=blue") == ("F", 8, "blue")
