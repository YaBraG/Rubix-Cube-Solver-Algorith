import pytest

from rubiks_solver.robot_moves import (
    convert_move_to_robot_command,
    convert_solution_to_robot_commands,
)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("U", ("white", 90)),
        ("U'", ("white", -90)),
        ("U2", ("white", 180)),
        ("D", ("yellow", 90)),
        ("D'", ("yellow", -90)),
        ("D2", ("yellow", 180)),
        ("F", ("green", 90)),
        ("F'", ("green", -90)),
        ("F2", ("green", 180)),
        ("B", ("blue", 90)),
        ("B'", ("blue", -90)),
        ("B2", ("blue", 180)),
        ("R", ("red", 90)),
        ("R'", ("red", -90)),
        ("R2", ("red", 180)),
        ("L", ("orange", 90)),
        ("L'", ("orange", -90)),
        ("L2", ("orange", 180)),
    ],
)
def test_convert_move_to_robot_command(move, expected):
    assert convert_move_to_robot_command(move) == expected


@pytest.mark.parametrize(
    "move",
    [
        "",
        " ",
        "X",
        "X2",
        "R3",
        "RR",
        "U''",
    ],
)
def test_convert_move_to_robot_command_rejects_invalid_input(move):
    with pytest.raises(ValueError):
        convert_move_to_robot_command(move)


def test_convert_solution_to_robot_commands_handles_multiple_moves():
    assert convert_solution_to_robot_commands("R U R' U'") == [
        ("red", 90),
        ("white", 90),
        ("red", -90),
        ("white", -90),
    ]


def test_convert_solution_to_robot_commands_handles_empty_solution():
    assert convert_solution_to_robot_commands("") == []


def test_convert_solution_to_robot_commands_handles_front_face_moves():
    assert convert_solution_to_robot_commands("F F' F2") == [
        ("green", 90),
        ("green", -90),
        ("green", 180),
    ]
