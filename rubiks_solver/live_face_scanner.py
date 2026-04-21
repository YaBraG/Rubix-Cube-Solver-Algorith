"""Live camera scanner for one Rubik's Cube face at a time."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .image_sampling import rgb_to_hsv_degrees


VALID_FACES = ("U", "R", "F", "D", "L", "B")


def positive_int(value: str) -> int:
    """Argparse helper for positive integers."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-live-scanner",
        description=(
            "Open a live webcam feed, align one Rubik's Cube face inside a 3x3 grid, "
            "and sample RGB/HSV values for that face."
        ),
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera index. Default: 0.")
    parser.add_argument(
        "--face",
        choices=VALID_FACES,
        help="Optional face label for this scan: U, R, F, D, L, or B.",
    )
    parser.add_argument(
        "--grid-size",
        type=positive_int,
        help=(
            "Full 3x3 overlay size in pixels. Larger values help cover a larger cube face."
        ),
    )
    parser.add_argument(
        "--patch-size",
        type=positive_int,
        help=(
            "Square sampling patch size in pixels. Keep it small enough to avoid black borders."
        ),
    )
    parser.add_argument(
        "--output",
        help="Optional path to save the most recent sampled face as JSON.",
    )
    return parser


def generate_grid_centers(center_x: int, center_y: int, size: int) -> list[tuple[int, int]]:
    """Generate 3x3 cell centers in row-major order."""
    cell_size = size / 3
    start_x = center_x - size / 2
    start_y = center_y - size / 2
    centers = []
    for row in range(3):
        for col in range(3):
            x = round(start_x + (col + 0.5) * cell_size)
            y = round(start_y + (row + 0.5) * cell_size)
            centers.append((x, y))
    return centers


def average_patch_rgb(frame: Any, center_x: int, center_y: int, patch_size: int) -> dict[str, int]:
    """Average a square BGR frame patch and return RGB values."""
    height = len(frame)
    width = len(frame[0])
    radius = max(0, patch_size // 2)
    left = max(0, center_x - radius)
    right = min(width, center_x + radius + 1)
    top = max(0, center_y - radius)
    bottom = min(height, center_y + radius + 1)

    total_r = 0
    total_g = 0
    total_b = 0
    count = 0
    for y in range(top, bottom):
        for x in range(left, right):
            b, g, r = frame[y][x]
            total_r += int(r)
            total_g += int(g)
            total_b += int(b)
            count += 1

    if count == 0:
        raise ValueError("Patch sampling found no pixels.")

    return {
        "r": round(total_r / count),
        "g": round(total_g / count),
        "b": round(total_b / count),
    }


def classify_hsv_color(hsv: dict[str, float]) -> str:
    """Experimental HSV classifier for Rubik's Cube colors."""
    h = hsv["h"]
    s = hsv["s"]
    v = hsv["v"]

    if v < 0.12:
        return "unknown"
    if s < 0.2 and v > 0.6:
        return "white"
    if s < 0.35:
        return "unknown"
    if h <= 12 or h >= 345:
        return "red"
    if 15 <= h <= 35 and s >= 0.45:
        return "orange"
    if 40 <= h <= 65 and s >= 0.35:
        return "yellow"
    if 70 <= h <= 160:
        return "green"
    if 180 <= h <= 250:
        return "blue"
    return "unknown"


def sample_face(
    frame: Any,
    *,
    center_x: int,
    center_y: int,
    size: int,
    sample_patch_size: int,
) -> list[dict[str, Any]]:
    """Sample 9 cells from the live frame."""
    samples = []
    for index, (x, y) in enumerate(generate_grid_centers(center_x, center_y, size)):
        rgb = average_patch_rgb(frame, x, y, sample_patch_size)
        hsv = rgb_to_hsv_degrees(rgb["r"], rgb["g"], rgb["b"])
        samples.append(
            {
                "index": index,
                "rgb": rgb,
                "hsv": hsv,
                "classified_color": classify_hsv_color(hsv),
            }
        )
    return samples


def build_scan_payload(
    *,
    camera_index: int,
    face: str | None,
    center_x: int,
    center_y: int,
    size: int,
    sample_patch_size: int,
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build JSON payload for one sampled face."""
    payload = {
        "source": "live_camera",
        "camera_index": camera_index,
        "grid": {
            "center_x": center_x,
            "center_y": center_y,
            "size": size,
            "sample_patch_size": sample_patch_size,
        },
        "samples": samples,
        "center": {
            "index": 4,
            "classified_color": samples[4]["classified_color"],
        },
    }
    if face is not None:
        payload["face"] = face
    return payload


def compute_default_grid_size(frame_width: int, frame_height: int) -> int:
    """Compute a larger, more usable default overlay size."""
    return max(180, round(min(frame_width, frame_height) * 0.42))


def save_scan_payload(output_path: str | Path, payload: dict[str, Any]) -> Path:
    """Save sampled payload to JSON."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_file


def print_help_summary() -> None:
    """Print keyboard help in terminal."""
    print(get_help_summary_text())


def get_help_summary_text() -> str:
    """Return help summary text for tests and overlays."""
    return "\n".join(
        [
            "Live scanner controls:",
            "  q = quit",
            "  s = sample current face",
            "  w/a/x/d or arrow keys = move grid",
            "  + / - = increase/decrease grid size",
            "  [ / ] = decrease/increase sample patch size",
            "  --grid-size sets full overlay size in pixels",
            "  --patch-size sets square sampling patch size in pixels",
            "  h = print this help",
        ]
    )


def draw_overlay(
    cv2: Any,
    frame: Any,
    *,
    center_x: int,
    center_y: int,
    size: int,
    sample_patch_size: int,
    preview_samples: list[dict[str, Any]] | None = None,
    face: str | None = None,
) -> None:
    """Draw 3x3 grid and optional classifications on the frame."""
    cell_size = round(size / 3)
    left = round(center_x - size / 2)
    top = round(center_y - size / 2)
    right = left + size
    bottom = top + size
    centers = generate_grid_centers(center_x, center_y, size)

    cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 255), 2)
    for row in range(1, 3):
        y = top + row * cell_size
        cv2.line(frame, (left, y), (right, y), (200, 200, 200), 1)
    for col in range(1, 3):
        x = left + col * cell_size
        cv2.line(frame, (x, top), (x, bottom), (200, 200, 200), 1)

    for index, (x, y) in enumerate(centers):
        color = (0, 255, 255) if index == 4 else (0, 255, 0)
        radius = max(3, sample_patch_size // 2)
        cv2.circle(frame, (x, y), radius, color, 2)

        if preview_samples is not None:
            label = preview_samples[index]["classified_color"]
            font_scale = 0.7 if index == 4 else 0.45
            thickness = 2 if index == 4 else 1
            cv2.putText(
                frame,
                label,
                (x - 28, y - radius - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )

    title = f"Live Face Scanner {face or ''}".strip()
    cv2.putText(
        frame,
        title,
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"grid {size} | patch {sample_patch_size} | face {face or '-'}",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "s sample | q quit | h help",
        (20, 88),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def run_live_scanner(
    camera_index: int,
    face: str | None = None,
    output: str | None = None,
    *,
    grid_size: int | None = None,
    patch_size: int | None = None,
) -> int:
    """Run the live scanner loop with OpenCV."""
    try:
        import cv2
    except ImportError:
        print("Error: OpenCV is required for live_face_scanner. Install opencv-python.")
        return 2

    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        print(f"Error: Could not open camera {camera_index}.")
        return 2

    ok, frame = capture.read()
    if not ok:
        capture.release()
        print(f"Error: Could not read from camera {camera_index}.")
        return 2

    frame_height, frame_width = frame.shape[:2]
    center_x = frame_width // 2
    center_y = frame_height // 2
    size = grid_size or compute_default_grid_size(frame_width, frame_height)
    size = min(size, min(frame_width, frame_height))
    sample_patch_size = patch_size or 12
    last_payload = None

    print_help_summary()

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("Warning: Failed to read frame from camera.")
                break

            preview_samples = sample_face(
                frame,
                center_x=center_x,
                center_y=center_y,
                size=size,
                sample_patch_size=sample_patch_size,
            )
            draw_overlay(
                cv2,
                frame,
                center_x=center_x,
                center_y=center_y,
                size=size,
                sample_patch_size=sample_patch_size,
                preview_samples=preview_samples,
                face=face,
            )
            cv2.imshow("Rubik's Live Face Scanner", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 255:
                continue
            if key == ord("q"):
                break
            if key == ord("h"):
                print_help_summary()
            elif key == ord("s"):
                samples = sample_face(
                    frame,
                    center_x=center_x,
                    center_y=center_y,
                    size=size,
                    sample_patch_size=sample_patch_size,
                )
                last_payload = build_scan_payload(
                    camera_index=camera_index,
                    face=face,
                    center_x=center_x,
                    center_y=center_y,
                    size=size,
                    sample_patch_size=sample_patch_size,
                    samples=samples,
                )
                print("Sampled face:")
                for sample in samples:
                    print(
                        f"  {sample['index']}: {sample['classified_color']} "
                        f"RGB={sample['rgb']} HSV={sample['hsv']}"
                    )
                print(f"Center sticker: {last_payload['center']}")
                if output:
                    saved = save_scan_payload(output, last_payload)
                    print(f"Saved scan: {saved}")
            elif key in (ord("a"), 81):
                center_x = max(size // 2, center_x - 10)
            elif key in (ord("d"), 83):
                center_x = min(frame_width - size // 2, center_x + 10)
            elif key in (ord("w"), 82):
                center_y = max(size // 2, center_y - 10)
            elif key in (ord("s"),):  # pragma: no cover - handled above
                pass
            elif key in (ord("x"), 84):
                center_y = min(frame_height - size // 2, center_y + 10)
            elif key in (ord("+"), ord("=")):
                size = min(min(frame_width, frame_height), size + 15)
            elif key == ord("-"):
                size = max(90, size - 15)
            elif key == ord("["):
                sample_patch_size = max(3, sample_patch_size - 2)
            elif key == ord("]"):
                sample_patch_size = min(51, sample_patch_size + 2)

            center_x = min(max(size // 2, center_x), frame_width - size // 2)
            center_y = min(max(size // 2, center_y), frame_height - size // 2)
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_live_scanner(
        args.camera,
        face=args.face,
        output=args.output,
        grid_size=args.grid_size,
        patch_size=args.patch_size,
    )


if __name__ == "__main__":
    raise SystemExit(main())
