"""Rubik's Cube solver package."""

from .capture_guide import DEFAULT_CAPTURE_PRESET, build_capture_guide
from .color_state import ColorStateError, colors_to_facelet_string
from .face_input import (
    FACE_ROTATION_PRESETS,
    FaceInputError,
    assemble_faces_to_color_string,
    assemble_faces_to_facelet_string,
)
from .robot_moves import DEFAULT_FACE_COLOR_MAPPING, convert_solution_to_robot_commands
from .solver import solve_cube
from .validation import CubeValidationError, validate_cube_state

__all__ = [
    "ColorStateError",
    "CubeValidationError",
    "DEFAULT_FACE_COLOR_MAPPING",
    "DEFAULT_CAPTURE_PRESET",
    "FACE_ROTATION_PRESETS",
    "FaceInputError",
    "assemble_faces_to_color_string",
    "assemble_faces_to_facelet_string",
    "build_capture_guide",
    "colors_to_facelet_string",
    "convert_solution_to_robot_commands",
    "solve_cube",
    "validate_cube_state",
]
