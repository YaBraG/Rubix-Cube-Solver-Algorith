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

SOLVED_SHORTHAND_COLOR_STATE = (
    "w w w w w w w w w "
    "r r r r r r r r r "
    "g g g g g g g g g "
    "y y y y y y y y y "
    "o o o o o o o o o "
    "b b b b b b b b b"
)

SOLVED_FACELET_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_colors_to_facelet_string_accepts_valid_input():
    assert colors_to_facelet_string(SOLVED_COLOR_STATE) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_is_case_insensitive():
    mixed_case = SOLVED_COLOR_STATE.title()
    assert colors_to_facelet_string(mixed_case) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_accepts_shorthand_tokens():
    assert colors_to_facelet_string(SOLVED_SHORTHAND_COLOR_STATE) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_accepts_uppercase_shorthand_tokens():
    assert colors_to_facelet_string(SOLVED_SHORTHAND_COLOR_STATE.upper()) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_accepts_mixed_full_names_and_shorthand():
    mixed_state = (
        "white w white w white w white w white "
        "red r red r red r red r red "
        "green g green g green g green g green "
        "yellow y yellow y yellow y yellow y yellow "
        "orange o orange o orange o orange o orange "
        "blue b blue b blue b blue b blue"
    )
    assert colors_to_facelet_string(mixed_state) == SOLVED_FACELET_STATE


def test_colors_to_facelet_string_rejects_wrong_color_count():
    with pytest.raises(ColorStateError, match="54 color tokens"):
        colors_to_facelet_string("white " * 53)


def test_colors_to_facelet_string_rejects_unknown_token():
    invalid_state = SOLVED_SHORTHAND_COLOR_STATE.replace("b", "p", 1)
    with pytest.raises(ColorStateError, match="unknown tokens"):
        colors_to_facelet_string(invalid_state)


def test_colors_to_facelet_string_rejects_wrong_per_color_counts():
    invalid_state = SOLVED_SHORTHAND_COLOR_STATE.replace("b", "w", 1)
    with pytest.raises(ColorStateError, match="wrong color counts"):
        colors_to_facelet_string(invalid_state)
