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
        ("R", ("red", 90)),
        ("R'", ("red", -90)),
        ("R2", ("red", 180)),
    ],
)
def test_convert_move_to_robot_command(move, expected):
    assert convert_move_to_robot_command(move) == expected


def test_convert_solution_to_robot_commands_handles_multiple_moves():
    assert convert_solution_to_robot_commands("R U R' U'") == [
        ("red", 90),
        ("white", 90),
        ("red", -90),
        ("white", -90),
    ]


def test_convert_solution_to_robot_commands_handles_empty_solution():
    assert convert_solution_to_robot_commands("") == []
