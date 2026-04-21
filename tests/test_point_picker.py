import json

import pytest

from rubiks_solver.point_picker import (
    VALID_STICKER_COLORS,
    PointPickerError,
    build_point_payload,
    build_point_plan,
    ensure_output_path,
    validate_sticker_color,
    write_point_file,
)


def test_build_point_plan_photo_1():
    plan = build_point_plan("photo_1")

    assert len(plan) == 27
    assert plan[0] == {
        "label": "U0",
        "face": "U",
        "index": 0,
        "face_color": "white",
    }
    assert plan[9]["label"] == "F0"
    assert plan[18]["label"] == "L0"
    assert plan[-1]["label"] == "L8"
    assert plan[-1]["face_color"] == "orange"


def test_build_point_plan_photo_2():
    plan = build_point_plan("photo_2")

    assert len(plan) == 27
    assert plan[0]["label"] == "D0"
    assert plan[0]["face_color"] == "yellow"
    assert plan[9]["label"] == "B0"
    assert plan[9]["face_color"] == "blue"
    assert plan[18]["label"] == "R0"
    assert plan[-1]["label"] == "R8"
    assert plan[-1]["face_color"] == "red"


def test_build_point_payload_structure():
    clicked_points = [
        {"x": index, "y": index + 10, "sticker_color": "red"} for index in range(27)
    ]

    payload = build_point_payload("photo_1", clicked_points)

    assert payload["image_role"] == "photo_1"
    assert payload["capture_preset"] == "capture-v1"
    assert len(payload["points"]) == 27
    assert payload["points"][0]["label"] == "U0"
    assert payload["points"][0]["face_color"] == "white"
    assert payload["points"][0]["sticker_color"] == "red"
    assert payload["points"][0]["x"] == 0
    assert payload["points"][-1]["label"] == "L8"


def test_build_point_payload_requires_sticker_color():
    clicked_points = [{"x": index, "y": index + 10} for index in range(27)]

    with pytest.raises(PointPickerError, match="missing sticker_color"):
        build_point_payload("photo_1", clicked_points)


def test_validate_sticker_color_accepts_supported_values():
    assert set(VALID_STICKER_COLORS) == {
        "white",
        "yellow",
        "green",
        "blue",
        "red",
        "orange",
    }
    assert validate_sticker_color("Red") == "red"


def test_validate_sticker_color_rejects_invalid_value():
    with pytest.raises(PointPickerError, match="Invalid sticker color"):
        validate_sticker_color("purple")


def test_refuse_overwrite_without_force(tmp_path):
    output_path = tmp_path / "points.json"
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(PointPickerError, match="Use --force"):
        ensure_output_path(output_path, force=False)


def test_allow_overwrite_with_force(tmp_path):
    output_path = tmp_path / "points.json"
    output_path.write_text("existing", encoding="utf-8")

    resolved = ensure_output_path(output_path, force=True)

    assert resolved == output_path


def test_write_point_file_creates_json(tmp_path):
    output_path = tmp_path / "points.json"
    clicked_points = [
        {"x": index * 2, "y": index * 3, "sticker_color": "blue"} for index in range(27)
    ]

    written = write_point_file(output_path, "photo_2", clicked_points, force=False)

    saved = json.loads(written.read_text(encoding="utf-8"))
    assert saved["image_role"] == "photo_2"
    assert saved["points"][0]["label"] == "D0"
    assert saved["points"][0]["face_color"] == "yellow"
    assert saved["points"][0]["sticker_color"] == "blue"
    assert saved["points"][-1]["label"] == "R8"
