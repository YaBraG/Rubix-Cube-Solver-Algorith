import pytest

from rubiks_solver.validation import CubeValidationError, validate_cube_state


SOLVED_CUBE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_validate_cube_state_accepts_solved_cube():
    assert validate_cube_state(SOLVED_CUBE) == SOLVED_CUBE


def test_validate_cube_state_rejects_wrong_length():
    with pytest.raises(CubeValidationError, match="54 characters"):
        validate_cube_state("U" * 53)


def test_validate_cube_state_rejects_invalid_letters():
    invalid_state = SOLVED_CUBE[:-1] + "X"
    with pytest.raises(CubeValidationError, match="invalid face letters"):
        validate_cube_state(invalid_state)


def test_validate_cube_state_rejects_wrong_face_counts():
    invalid_state = "U" * 54
    with pytest.raises(CubeValidationError, match="wrong face counts"):
        validate_cube_state(invalid_state)
