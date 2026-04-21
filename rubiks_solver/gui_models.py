"""Shared GUI state helpers for manual and camera-review workflows."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .color_state import DEFAULT_FACE_TO_PRIMARY_COLOR
from .live_face_scanner import DEFAULT_FACE_SEQUENCE
from .session_solver import extract_session_faces, load_scan_session


UNKNOWN_COLOR = "unknown"
DISPLAY_LETTERS = {
    "white": "W",
    "yellow": "Y",
    "green": "G",
    "blue": "B",
    "red": "R",
    "orange": "O",
    "unknown": "U",
}
DISPLAY_COLORS = {
    "white": "#f5f5f5",
    "yellow": "#f3d34a",
    "green": "#48a65a",
    "blue": "#4f77d9",
    "red": "#d64c4c",
    "orange": "#e6923a",
    "unknown": "#8a8a8a",
}
TEXT_COLORS = {
    "white": "#111111",
    "yellow": "#111111",
    "green": "#ffffff",
    "blue": "#ffffff",
    "red": "#ffffff",
    "orange": "#111111",
    "unknown": "#ffffff",
}
EDITABLE_INDEXES = (0, 1, 2, 3, 5, 6, 7, 8)


def create_empty_editor_faces() -> dict[str, list[str]]:
    """Create six faces with virtual centers and unknown outer stickers."""
    return {
        face: [
            DEFAULT_FACE_TO_PRIMARY_COLOR[face] if index == 4 else UNKNOWN_COLOR
            for index in range(9)
        ]
        for face in DEFAULT_FACE_SEQUENCE
    }


def clone_faces(faces: dict[str, list[str]]) -> dict[str, list[str]]:
    return {face: list(colors) for face, colors in faces.items()}


def inject_virtual_centers(faces: dict[str, list[str]]) -> dict[str, list[str]]:
    """Force known virtual center colors into a face map."""
    updated = clone_faces(faces)
    for face in DEFAULT_FACE_SEQUENCE:
        updated[face][4] = DEFAULT_FACE_TO_PRIMARY_COLOR[face]
    return updated


def face_rows(faces: dict[str, list[str]]) -> dict[str, list[str]]:
    """Return face rows using one-letter shorthand for diagnostics."""
    normalized = inject_virtual_centers(faces)
    rows: dict[str, list[str]] = {}
    for face in DEFAULT_FACE_SEQUENCE:
        colors = normalized[face]
        rows[face] = [
            " ".join(DISPLAY_LETTERS[color].lower() for color in colors[0:3]),
            " ".join(DISPLAY_LETTERS[color].lower() for color in colors[3:6]),
            " ".join(DISPLAY_LETTERS[color].lower() for color in colors[6:9]),
        ]
    return rows


def count_editor_colors(faces: dict[str, list[str]]) -> dict[str, int]:
    counts = Counter()
    for colors in inject_virtual_centers(faces).values():
        counts.update(colors)
    ordered = list(DEFAULT_FACE_TO_PRIMARY_COLOR.values()) + [UNKNOWN_COLOR]
    return {color: counts.get(color, 0) for color in ordered}


def unknown_positions(faces: dict[str, list[str]]) -> list[str]:
    positions: list[str] = []
    normalized = inject_virtual_centers(faces)
    for face in DEFAULT_FACE_SEQUENCE:
        for index, color in enumerate(normalized[face]):
            if color == UNKNOWN_COLOR:
                positions.append(f"{face}{index}")
    return positions


def editor_faces_to_color_lists(faces: dict[str, list[str]]) -> dict[str, list[str]]:
    return inject_virtual_centers(faces)


def load_editor_faces_from_session(session_dir: str | Path) -> dict[str, list[str]]:
    session_payloads = load_scan_session(session_dir)
    faces, _virtual_notes = extract_session_faces(session_payloads)
    return inject_virtual_centers(faces)


def summarize_editor_state(faces: dict[str, list[str]]) -> dict[str, Any]:
    normalized = inject_virtual_centers(faces)
    return {
        "faces": normalized,
        "rows": face_rows(normalized),
        "color_counts": count_editor_colors(normalized),
        "unknown_positions": unknown_positions(normalized),
    }
