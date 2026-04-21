import json

import pytest
from PIL import Image

from rubiks_solver.image_sampling import (
    ImageSamplingError,
    load_points_file,
    rgb_to_hsv_degrees,
    sample_image_points,
)


def create_test_image(path):
    image = Image.new("RGB", (4, 4), color=(0, 0, 0))
    image.putpixel((1, 1), (255, 0, 0))
    image.putpixel((2, 2), (0, 255, 0))
    image.save(path)


def create_points_file(path, points):
    payload = {
        "image_role": "photo_1",
        "capture_preset": "capture-v1",
        "points": points,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_rgb_sampling_from_known_image(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    create_test_image(image_path)
    create_points_file(
        points_path,
        [{"label": "U0", "face": "U", "index": 0, "expected_color": "red", "x": 1, "y": 1}],
    )

    report = sample_image_points(image_path, points_path)

    assert report["sample_count"] == 1
    assert report["samples"][0]["rgb"] == {"r": 255, "g": 0, "b": 0}


def test_rgb_to_hsv_conversion_sanity_checks():
    assert rgb_to_hsv_degrees(255, 0, 0) == {"h": 0.0, "s": 1.0, "v": 1.0}
    green_hsv = rgb_to_hsv_degrees(0, 255, 0)
    assert green_hsv["h"] == 120.0
    assert green_hsv["s"] == 1.0
    assert green_hsv["v"] == 1.0


def test_valid_points_json_loads_successfully(tmp_path):
    points_path = tmp_path / "points.json"
    create_points_file(points_path, [{"label": "U0", "x": 0, "y": 0}])

    loaded = load_points_file(points_path)

    assert isinstance(loaded["points"], list)


def test_missing_image_path_error(tmp_path):
    points_path = tmp_path / "points.json"
    create_points_file(points_path, [{"label": "U0", "x": 0, "y": 0}])

    with pytest.raises(ImageSamplingError, match="Image file not found"):
        sample_image_points(tmp_path / "missing.png", points_path)


def test_missing_points_file_error(tmp_path):
    image_path = tmp_path / "test.png"
    create_test_image(image_path)

    with pytest.raises(ImageSamplingError, match="Points file not found"):
        sample_image_points(image_path, tmp_path / "missing.json")


def test_out_of_bounds_coordinate_error(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    create_test_image(image_path)
    create_points_file(points_path, [{"label": "U0", "x": 10, "y": 10}])

    with pytest.raises(ImageSamplingError, match="outside image bounds"):
        sample_image_points(image_path, points_path)


def test_invalid_face_error(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    create_test_image(image_path)
    create_points_file(points_path, [{"label": "U0", "face": "X", "x": 1, "y": 1}])

    with pytest.raises(ImageSamplingError, match="invalid face"):
        sample_image_points(image_path, points_path)


def test_invalid_index_error(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    create_test_image(image_path)
    create_points_file(points_path, [{"label": "U0", "index": 9, "x": 1, "y": 1}])

    with pytest.raises(ImageSamplingError, match="invalid index"):
        sample_image_points(image_path, points_path)


def test_json_report_contains_expected_fields(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    output_path = tmp_path / "report.json"
    create_test_image(image_path)
    create_points_file(
        points_path,
        [{"label": "U0", "face": "U", "index": 0, "expected_color": "red", "x": 1, "y": 1}],
    )

    report = sample_image_points(image_path, points_path, output_path=output_path)

    assert report["image_size"] == {"width": 4, "height": 4}
    assert report["sample_count"] == 1
    assert "rgb" in report["samples"][0]
    assert "hsv" in report["samples"][0]
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["sample_count"] == 1


def test_annotated_output_file_is_created(tmp_path):
    image_path = tmp_path / "test.png"
    points_path = tmp_path / "points.json"
    output_path = tmp_path / "report.json"
    annotated_path = tmp_path / "annotated.jpg"
    create_test_image(image_path)
    create_points_file(points_path, [{"label": "U0", "x": 1, "y": 1}])

    sample_image_points(
        image_path,
        points_path,
        output_path=output_path,
        annotated_output_path=annotated_path,
    )

    assert annotated_path.exists()
