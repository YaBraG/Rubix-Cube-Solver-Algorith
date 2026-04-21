import json

from rubiks_solver.gui_app import (
    build_scanner_log_path,
    get_popup_color_options,
    resolve_color_shortcut,
)
from rubiks_solver.gui_models import (
    DISPLAY_COLORS,
    DISPLAY_LETTERS,
    TEXT_COLORS,
    count_editor_colors,
    create_empty_editor_faces,
    inject_virtual_centers,
    load_editor_faces_from_session,
    summarize_editor_state,
)
from rubiks_solver.gui_solver import build_result_payload, build_facelet_string_from_editor, solve_editor_faces


def write_face_scan(session_dir, face, colors):
    payload = {
        "face": face,
        "samples": [{"index": index, "classified_color": color} for index, color in enumerate(colors)],
    }
    path = session_dir / f"{face.lower()}_face_scan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_empty_manual_grid_initialization():
    faces = create_empty_editor_faces()

    assert faces["U"][4] == "white"
    assert faces["R"][4] == "red"
    assert faces["F"][4] == "green"
    assert faces["D"][4] == "yellow"
    assert faces["L"][4] == "orange"
    assert faces["B"][4] == "blue"
    assert faces["U"][0] == "unknown"
    assert faces["B"][8] == "unknown"


def test_virtual_centers_injected_correctly():
    faces = create_empty_editor_faces()
    faces["U"][4] = "blue"
    faces["R"][4] = "white"

    updated = inject_virtual_centers(faces)

    assert updated["U"][4] == "white"
    assert updated["R"][4] == "red"


def test_grid_to_face_string_conversion():
    faces = {
        "U": ["white"] * 9,
        "R": ["red"] * 9,
        "F": ["green"] * 9,
        "D": ["yellow"] * 9,
        "L": ["orange"] * 9,
        "B": ["blue"] * 9,
    }

    facelet_string = build_facelet_string_from_editor(faces)

    assert facelet_string == "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_color_count_validation_and_unknown_detection():
    faces = create_empty_editor_faces()
    summary = summarize_editor_state(faces)

    assert summary["color_counts"]["unknown"] == 48
    assert "U0" in summary["unknown_positions"]
    assert "B8" in summary["unknown_positions"]


def test_gui_solve_helper_catches_wrong_color_counts_before_solver():
    faces = {
        "U": ["white"] * 9,
        "R": ["red"] * 9,
        "F": ["green"] * 9,
        "D": ["yellow"] * 9,
        "L": ["orange"] * 8 + ["white"],
        "B": ["blue"] * 9,
    }

    result = solve_editor_faces(faces)

    assert result["success"] is False
    assert "Color counts are invalid" in result["error"]
    assert "white: 10" in result["error"]
    assert "orange: 8" in result["error"]


def test_solving_solved_cube_state_through_gui_helper():
    faces = {
        "U": ["white"] * 9,
        "R": ["red"] * 9,
        "F": ["green"] * 9,
        "D": ["yellow"] * 9,
        "L": ["orange"] * 9,
        "B": ["blue"] * 9,
    }

    result = solve_editor_faces(faces)

    assert result["success"] is True
    assert result["solution"] == ""
    assert result["commands"] == []


def test_converting_session_scan_data_into_editor_state(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    write_face_scan(tmp_path, "U", ["red", "white", "white", "white", "blue", "white", "white", "white", "white"])
    write_face_scan(tmp_path, "R", ["red"] * 9)
    write_face_scan(tmp_path, "F", ["green"] * 9)
    write_face_scan(tmp_path, "D", ["yellow"] * 9)
    write_face_scan(tmp_path, "L", ["orange"] * 9)
    write_face_scan(tmp_path, "B", ["blue"] * 9)

    faces = load_editor_faces_from_session(tmp_path)

    assert faces["U"][0] == "red"
    assert faces["U"][4] == "white"


def test_result_payload_creation_for_success():
    faces = {
        "U": ["white"] * 9,
        "R": ["red"] * 9,
        "F": ["green"] * 9,
        "D": ["yellow"] * 9,
        "L": ["orange"] * 9,
        "B": ["blue"] * 9,
    }

    payload = build_result_payload(
        faces=faces,
        solution="R U",
        commands=[("red", 90), ("white", 90)],
    )

    assert payload["success"] is True
    assert payload["move_count"] == 2
    assert payload["commands"][0] == {"color": "red", "angle": 90}


def test_result_payload_creation_for_error():
    faces = create_empty_editor_faces()

    payload = build_result_payload(
        faces=faces,
        solution=None,
        commands=[],
        error="Unknown stickers remain.",
    )

    assert payload["success"] is False
    assert payload["error"] == "Unknown stickers remain."


def test_count_editor_colors_orders_known_and_unknown():
    counts = count_editor_colors(create_empty_editor_faces())

    assert counts["white"] == 1
    assert counts["yellow"] == 1
    assert counts["green"] == 1
    assert counts["blue"] == 1
    assert counts["red"] == 1
    assert counts["orange"] == 1
    assert counts["unknown"] == 48


def test_display_mapping_covers_all_colors():
    for color in ("white", "yellow", "green", "blue", "red", "orange", "unknown"):
        assert color in DISPLAY_COLORS
        assert color in TEXT_COLORS
        assert color in DISPLAY_LETTERS
        assert DISPLAY_COLORS[color].startswith("#")
        assert TEXT_COLORS[color].startswith("#")


def test_letter_shortcut_mapping():
    assert resolve_color_shortcut("W") == "white"
    assert resolve_color_shortcut("y") == "yellow"
    assert resolve_color_shortcut("G") == "green"
    assert resolve_color_shortcut("b") == "blue"
    assert resolve_color_shortcut("R") == "red"
    assert resolve_color_shortcut("o") == "orange"
    assert resolve_color_shortcut("U") == "unknown"


def test_number_shortcut_mapping():
    assert resolve_color_shortcut("1") == "white"
    assert resolve_color_shortcut("2") == "yellow"
    assert resolve_color_shortcut("3") == "green"
    assert resolve_color_shortcut("4") == "blue"
    assert resolve_color_shortcut("5") == "red"
    assert resolve_color_shortcut("6") == "orange"
    assert resolve_color_shortcut("7") == "unknown"


def test_invalid_shortcut_returns_no_color():
    assert resolve_color_shortcut("9") is None
    assert resolve_color_shortcut("q") is None


def test_popup_color_list_contains_all_colors():
    assert get_popup_color_options() == [
        "white",
        "yellow",
        "green",
        "blue",
        "red",
        "orange",
        "unknown",
    ]


def test_scanner_log_path_helper(tmp_path):
    assert build_scanner_log_path(tmp_path) == tmp_path / "scanner_log.txt"
