import pytest

from rubiks_solver.color_state import ColorStateError, colors_to_facelet_string


SOLVED_COLOR_STATE = (
    "white white white white white white white white white "
    "red red red red red red red red red "
    "green green green green green green green green green "
    "yellow yellow yellow yellow yellow yellow yellow yellow yellow "
    "orange orange orange orange orange orange orange orange orange "
    "blue blue blue blue blue blue blue blue blue"
)

SOLVED_FACELET_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_colors_to_facelet_string_accepts_valid_input():
    assert colors_to_facelet_string(SOLVED_COLOR_STATE) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_is_case_insensitive():
    mixed_case = SOLVED_COLOR_STATE.title()
    assert colors_to_facelet_string(mixed_case) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_rejects_wrong_color_count():
    with pytest.raises(ColorStateError, match="54 colors"):
        colors_to_facelet_string("white " * 53)


def test_colors_to_facelet_string_rejects_unknown_color():
    invalid_state = SOLVED_COLOR_STATE.replace("blue", "purple", 1)
    with pytest.raises(ColorStateError, match="unknown colors"):
        colors_to_facelet_string(invalid_state)


def test_colors_to_facelet_string_rejects_wrong_per_color_counts():
    invalid_state = SOLVED_COLOR_STATE.replace("blue", "white", 1)
    with pytest.raises(ColorStateError, match="wrong color counts"):
        colors_to_facelet_string(invalid_state)
