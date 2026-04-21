"""Manual capture guide text for current two-photo workflow."""

from pathlib import Path


DEFAULT_CAPTURE_PRESET = "capture-v1"


def build_capture_guide(photo1: str | None = None, photo2: str | None = None) -> str:
    """Build a plain-text guide for manual face entry from two photos."""
    lines = [
        "Capture guide",
        "",
        f"Preset: {DEFAULT_CAPTURE_PRESET}",
        "",
        "Confirmed orientation:",
        "- White = Up",
        "- Yellow = Down",
        "- Green = Front",
        "",
        "Photo 1 expected faces:",
        "- U = white face",
        "- F = green face",
        "- L = orange face",
        "",
        "Photo 2 expected faces:",
        "- D = yellow face",
        "- B = blue face",
        "- R = red face",
        "",
        "Read each face left-to-right, top-to-bottom as you see it in the photo.",
        "",
        "Use these arguments:",
        "- --u",
        "- --f",
        "- --l",
        "- --d",
        "- --b",
        "- --r",
        "",
        "Command template:",
        'python -m rubiks_solver.cli --faces --u "..." --f "..." --l "..." --d "..." --b "..." --r "..."',
        "",
        "Accepted shorthand:",
        "- w = white",
        "- y = yellow",
        "- g = green",
        "- b = blue",
        "- r = red",
        "- o = orange",
        "",
        "capture-v1 applies these rotations internally:",
        "- U = rotate counter-clockwise",
        "- R = keep",
        "- F = keep",
        "- D = keep",
        "- L = rotate counter-clockwise",
        "- B = rotate 180",
    ]

    for label, path_value in (("Photo 1 path", photo1), ("Photo 2 path", photo2)):
        if path_value is None:
            continue
        exists = Path(path_value).exists()
        status = "found" if exists else "warning: not found"
        lines.extend(
            [
                "",
                f"{label}: {path_value}",
                f"Status: {status}",
            ]
        )

    return "\n".join(lines)
