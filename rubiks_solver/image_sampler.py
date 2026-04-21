"""CLI for manual image color sampling."""

from __future__ import annotations

import argparse
import sys

from .image_sampling import ImageSamplingError, sample_image_points


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-sampler",
        description=(
            "Sample RGB and HSV values from an image using a manual JSON list of points."
        ),
    )
    parser.add_argument("--image", required=True, help="Path to the input image.")
    parser.add_argument("--points", required=True, help="Path to the sample points JSON file.")
    parser.add_argument("--output", required=True, help="Path to the output JSON report.")
    parser.add_argument(
        "--annotated-output",
        help="Optional path for a debug image with circles and labels drawn on sample points.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        report = sample_image_points(
            args.image,
            args.points,
            output_path=args.output,
            annotated_output_path=args.annotated_output,
        )
    except ImageSamplingError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Image: {report['image']}")
    print(f"Points file: {report['points_file']}")
    print(f"Sample count: {report['sample_count']}")
    print(f"Report written: {args.output}")
    if args.annotated_output:
        print(f"Annotated image written: {args.annotated_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
