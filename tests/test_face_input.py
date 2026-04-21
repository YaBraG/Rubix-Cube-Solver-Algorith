import pytest

from rubiks_solver.face_input import (
    FaceInputError,
    assemble_faces_to_color_string,
    parse_face_tokens,
    rotate_face_tokens,
)


RAW_SAMPLE_FACES = {
    "U": "y y g y w b r y w",
    "F": "b g w g g w y r r",
    "L": "o w r g o b b r o",
    "D": "r b b w y w g y w",
    "B": "y o o b b o y o o",
    "R": "g r b o r g w r g",
}

EXPECTED_CAPTURE_V1_COLOR_STRING = (
    "green blue white yellow white yellow yellow yellow red "
    "green red blue orange red green white red green "
    "blue green white green green white yellow red red "
    "red blue blue white yellow white green yellow white "
    "red blue orange white orange red orange green blue "
    "orange orange yellow orange blue blue orange orange yellow"
)


def test_rotate_face_tokens_none():
    tokens = [str(index) for index in range(9)]
    assert rotate_face_tokens(tokens, "none") == tokens


def test_rotate_face_tokens_clockwise():
    assert rotate_face_tokens([str(index) for index in range(9)], "clockwise") == [
        "6",
        "3",
        "0",
        "7",
        "4",
        "1",
        "8",
        "5",
        "2",
    ]


def test_rotate_face_tokens_counter_clockwise():
    assert rotate_face_tokens([str(index) for index in range(9)], "counter-clockwise") == [
        "2",
        "5",
        "8",
        "1",
        "4",
        "7",
        "0",
        "3",
        "6",
    ]


def test_rotate_face_tokens_180():
    assert rotate_face_tokens([str(index) for index in range(9)], "180") == [
        "8",
        "7",
        "6",
        "5",
        "4",
        "3",
        "2",
        "1",
        "0",
    ]


def test_parse_face_tokens_accepts_exactly_nine_tokens():
    assert parse_face_tokens("U", "w w w w w w w w w") == ["white"] * 9


def test_parse_face_tokens_rejects_wrong_token_count():
    with pytest.raises(FaceInputError, match="9 color tokens"):
        parse_face_tokens("U", "w w w")


def test_parse_face_tokens_rejects_unknown_token():
    with pytest.raises(FaceInputError, match="unknown tokens"):
        parse_face_tokens("U", "w w w w w w w w p")


def test_capture_v1_assembly_matches_expected_color_order():
    assert (
        assemble_faces_to_color_string(RAW_SAMPLE_FACES, orientation_preset="capture-v1")
        == EXPECTED_CAPTURE_V1_COLOR_STRING
    )
