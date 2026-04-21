"""Cube state validation helpers."""

from collections import Counter


FACE_ORDER = "URFDLB"
EXPECTED_LENGTH = 54
VALID_FACELETS = set(FACE_ORDER)


class CubeValidationError(ValueError):
    """Raised when cube state string is invalid."""


def validate_cube_state(cube_state: str) -> str:
    """Validate a 54-character Kociemba facelet string."""
    normalized = cube_state.strip().upper()

    if len(normalized) != EXPECTED_LENGTH:
        raise CubeValidationError(
            f"Cube state must be {EXPECTED_LENGTH} characters long."
        )

    if invalid_chars := sorted(set(normalized) - VALID_FACELETS):
        joined = ", ".join(invalid_chars)
        raise CubeValidationError(
            f"Cube state contains invalid face letters: {joined}."
        )

    counts = Counter(normalized)
    wrong_counts = {
        face: count for face, count in sorted(counts.items()) if count != 9
    }
    missing_faces = [face for face in FACE_ORDER if face not in counts]
    if wrong_counts or missing_faces:
        parts = [
            f"{face}={counts.get(face, 0)}" for face in FACE_ORDER if counts.get(face, 0) != 9
        ]
        detail = ", ".join(parts) if parts else "each face letter must appear 9 times"
        raise CubeValidationError(f"Cube state has wrong face counts: {detail}.")

    return normalized
