import json

from rubiks_solver.live_face_scanner import (
    build_parser,
    build_scan_payload,
    classify_hsv_color,
    generate_grid_centers,
    get_help_summary_text,
    average_patch_rgb,
    save_scan_payload,
)


def test_generate_grid_centers_for_3x3_layout():
    centers = generate_grid_centers(100, 100, 90)

    assert len(centers) == 9
    assert centers[0] == (70, 70)
    assert centers[4] == (100, 100)
    assert centers[8] == (130, 130)


def test_average_patch_rgb_on_generated_frame():
    frame = [
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [10, 20, 30], [10, 20, 30]],
        [[0, 0, 0], [10, 20, 30], [10, 20, 30]],
    ]

    rgb = average_patch_rgb(frame, 1, 1, 1)

    assert rgb == {"r": 30, "g": 20, "b": 10}


def test_classify_hsv_color_sanity_checks():
    assert classify_hsv_color({"h": 0.0, "s": 1.0, "v": 1.0}) == "red"
    assert classify_hsv_color({"h": 25.0, "s": 0.9, "v": 0.9}) == "orange"
    assert classify_hsv_color({"h": 55.0, "s": 0.8, "v": 0.95}) == "yellow"
    assert classify_hsv_color({"h": 120.0, "s": 0.8, "v": 0.7}) == "green"
    assert classify_hsv_color({"h": 220.0, "s": 0.8, "v": 0.7}) == "blue"
    assert classify_hsv_color({"h": 0.0, "s": 0.05, "v": 0.95}) == "white"


def test_unknown_classification_behavior():
    assert classify_hsv_color({"h": 300.0, "s": 0.8, "v": 0.8}) == "unknown"
    assert classify_hsv_color({"h": 40.0, "s": 0.1, "v": 0.2}) == "unknown"


def test_build_scan_payload_structure():
    samples = [
        {
            "index": index,
            "rgb": {"r": 1, "g": 2, "b": 3},
            "hsv": {"h": 10.0, "s": 0.5, "v": 0.6},
            "classified_color": "red",
        }
        for index in range(9)
    ]

    payload = build_scan_payload(
        camera_index=0,
        face="U",
        center_x=100,
        center_y=120,
        size=90,
        sample_patch_size=12,
        samples=samples,
    )

    assert payload["source"] == "live_camera"
    assert payload["camera_index"] == 0
    assert payload["face"] == "U"
    assert payload["grid"]["center_x"] == 100
    assert len(payload["samples"]) == 9
    assert payload["center"] == {"index": 4, "classified_color": "red"}


def test_invalid_face_argument_handling():
    parser = build_parser()
    try:
        parser.parse_args(["--camera", "0", "--face", "X"])
        assert False, "parse_args should fail for invalid face"
    except SystemExit as exc:
        assert exc.code == 2


def test_save_scan_payload(tmp_path):
    payload = {
        "source": "live_camera",
        "camera_index": 0,
        "samples": [],
        "center": {"index": 4, "classified_color": "white"},
    }

    output_path = save_scan_payload(tmp_path / "scan.json", payload)

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["source"] == "live_camera"


def test_help_summary_text_matches_controls():
    text = get_help_summary_text()

    assert "w/a/x/d or arrow keys = move grid" in text
    assert "s = sample current face" in text
    assert "WASD" not in text
