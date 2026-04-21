import pytest

from rubiks_solver.cli import main


SOLVED_COLOR_STATE = (
    "white white white white white white white white white "
    "red red red red red red red red red "
    "green green green green green green green green green "
    "yellow yellow yellow yellow yellow yellow yellow yellow yellow "
    "orange orange orange orange orange orange orange orange orange "
    "blue blue blue blue blue blue blue blue blue"
)

SOLVED_FACELET_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_cli_rejects_both_facelet_and_color_input(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main([SOLVED_FACELET_STATE, "--colors", SOLVED_COLOR_STATE])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "either a facelet cube state or --colors" in captured.err


def test_cli_solves_solved_cube_with_color_input(capsys):
    exit_code = main(["--colors", SOLVED_COLOR_STATE])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Cube already solved." in captured.out
    assert "No robot moves needed." in captured.out
