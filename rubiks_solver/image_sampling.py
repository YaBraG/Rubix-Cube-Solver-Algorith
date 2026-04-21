"""Image sampling helpers for manual color-debug workflows."""

from __future__ import annotations

import colorsys
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


VALID_FACES = set("URFDLB")


class ImageSamplingError(ValueError):
    """Raised when image sampling input is invalid."""


def rgb_to_hsv_degrees(r: int, g: int, b: int) -> dict[str, float]:
    """Convert 0-255 RGB values into HSV with degrees and 0-1 ranges."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return {
        "h": round(h * 360, 2),
        "s": round(s, 4),
        "v": round(v, 4),
    }


def load_points_file(points_path: str | Path) -> dict[str, Any]:
    """Load and validate manual sample points JSON."""
    path = Path(points_path)
    if not path.exists():
        raise ImageSamplingError(f"Points file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ImageSamplingError(f"Points file is not valid JSON: {path}") from exc

    if not isinstance(data, dict):
        raise ImageSamplingError("Points file must contain a JSON object.")
    if not isinstance(data.get("points"), list):
        raise ImageSamplingError("Points file must contain a 'points' list.")
    return data


def validate_point(point: dict[str, Any], image_width: int, image_height: int) -> dict[str, Any]:
    """Validate one point entry against schema and image bounds."""
    if not isinstance(point, dict):
        raise ImageSamplingError("Each point must be a JSON object.")

    label = point.get("label")
    x = point.get("x")
    y = point.get("y")
    if label is None or x is None or y is None:
        raise ImageSamplingError("Each point must include label, x, and y.")
    if not isinstance(label, str) or not label.strip():
        raise ImageSamplingError("Point label must be a non-empty string.")
    if not isinstance(x, int) or not isinstance(y, int):
        raise ImageSamplingError(f"Point {label} must use integer x and y coordinates.")
    if not (0 <= x < image_width and 0 <= y < image_height):
        raise ImageSamplingError(
            f"Point {label} is outside image bounds: ({x}, {y}) not within "
            f"{image_width}x{image_height}."
        )

    validated = {
        "label": label,
        "x": x,
        "y": y,
    }

    if "face" in point:
        face = point["face"]
        if not isinstance(face, str) or face not in VALID_FACES:
            raise ImageSamplingError(f"Point {label} has invalid face: {face}.")
        validated["face"] = face

    if "index" in point:
        index = point["index"]
        if not isinstance(index, int) or not (0 <= index <= 8):
            raise ImageSamplingError(f"Point {label} has invalid index: {index}.")
        validated["index"] = index

    if "face_color" in point:
        validated["face_color"] = point["face_color"]

    if "sticker_color" in point:
        validated["sticker_color"] = point["sticker_color"]

    if "expected_color" in point:
        validated["expected_color"] = point["expected_color"]

    return validated


def sample_image_points(
    image_path: str | Path,
    points_path: str | Path,
    *,
    output_path: str | Path | None = None,
    annotated_output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Sample RGB/HSV values from an image using manual point coordinates."""
    image_file = Path(image_path)
    if not image_file.exists():
        raise ImageSamplingError(f"Image file not found: {image_file}")

    points_data = load_points_file(points_path)

    with Image.open(image_file) as img:
        rgb_image = img.convert("RGB")
        width, height = rgb_image.size
        samples = []

        for raw_point in points_data["points"]:
            point = validate_point(raw_point, width, height)
            r, g, b = rgb_image.getpixel((point["x"], point["y"]))
            sample = {
                **point,
                "rgb": {"r": r, "g": g, "b": b},
                "hsv": rgb_to_hsv_degrees(r, g, b),
            }
            samples.append(sample)

        report = {
            "image": str(image_file),
            "image_size": {"width": width, "height": height},
            "points_file": str(Path(points_path)),
            "sample_count": len(samples),
            "samples": samples,
        }

        if "image_role" in points_data:
            report["image_role"] = points_data["image_role"]
        if "capture_preset" in points_data:
            report["capture_preset"] = points_data["capture_preset"]
        if "note" in points_data:
            report["note"] = points_data["note"]

        if output_path is not None:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

        if annotated_output_path is not None:
            annotated_file = Path(annotated_output_path)
            annotated_file.parent.mkdir(parents=True, exist_ok=True)
            annotate_image(rgb_image, samples, annotated_file)

    return report


def annotate_image(image: Image.Image, samples: list[dict[str, Any]], output_path: Path) -> None:
    """Draw simple circles and labels for sampled points."""
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    for sample in samples:
        x = sample["x"]
        y = sample["y"]
        radius = 8
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="red", width=2)
        draw.text((x + 10, y - 10), sample["label"], fill="red")

    annotated.save(output_path)
