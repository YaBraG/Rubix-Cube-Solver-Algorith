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

SOLVED_SHORTHAND_COLOR_STATE = (
    "w w w w w w w w w "
    "r r r r r r r r r "
    "g g g g g g g g g "
    "y y y y y y y y y "
    "o o o o o o o o o "
    "b b b b b b b b b"
)

SOLVED_FACELET_STATE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
SOLVED_U_FACE = "w w w w w w w w w"
SOLVED_R_FACE = "r r r r r r r r r"
SOLVED_F_FACE = "g g g g g g g g g"
SOLVED_D_FACE = "y y y y y y y y y"
SOLVED_L_FACE = "o o o o o o o o o"
SOLVED_B_FACE = "b b b b b b b b b"
RAW_SAMPLE_FACES = {
    "u": "y y g y w b r y w",
    "f": "b g w g g w y r r",
    "l": "o w r g o b b r o",
    "d": "r b b w y w g y w",
    "b": "y o o b b o y o o",
    "r": "g r b o r g w r g",
}


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


def test_cli_solves_solved_cube_with_shorthand_color_input(capsys):
    exit_code = main(["--colors", SOLVED_SHORTHAND_COLOR_STATE])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Cube already solved." in captured.out
    assert "No robot moves needed." in captured.out


def test_cli_solves_solved_cube_with_faces_input(capsys):
    exit_code = main(
        [
            "--faces",
            "--u",
            SOLVED_U_FACE,
            "--r",
            SOLVED_R_FACE,
            "--f",
            SOLVED_F_FACE,
            "--d",
            SOLVED_D_FACE,
            "--l",
            SOLVED_L_FACE,
            "--b",
            SOLVED_B_FACE,
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Cube already solved." in captured.out


def test_cli_rejects_faces_with_colors_conflict(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--faces", "--colors", SOLVED_COLOR_STATE, "--u", SOLVED_U_FACE])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "either --colors or --faces" in captured.err


def test_cli_rejects_missing_face_argument_in_faces_mode(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--faces",
                "--u",
                SOLVED_U_FACE,
                "--r",
                SOLVED_R_FACE,
                "--f",
                SOLVED_F_FACE,
                "--d",
                SOLVED_D_FACE,
                "--l",
                SOLVED_L_FACE,
            ]
        )

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "--faces requires all six face arguments" in captured.err


def test_cli_real_sample_faces_do_not_fail_as_impossible(capsys):
    exit_code = main(
        [
            "--faces",
            "--u",
            RAW_SAMPLE_FACES["u"],
            "--f",
            RAW_SAMPLE_FACES["f"],
            "--l",
            RAW_SAMPLE_FACES["l"],
            "--d",
            RAW_SAMPLE_FACES["d"],
            "--b",
            RAW_SAMPLE_FACES["b"],
            "--r",
            RAW_SAMPLE_FACES["r"],
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Solution:" in captured.out
    assert "Robot commands:" in captured.out


def test_capture_guide_exits_successfully(capsys):
    exit_code = main(["--capture-guide"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "capture-v1" in captured.out
    assert "Photo 1" in captured.out
    assert "Photo 2" in captured.out
    assert "--faces" in captured.out
    assert "w = white" in captured.out


def test_capture_guide_reports_existing_photo_paths(capsys):
    exit_code = main(
        [
            "--capture-guide",
            "--photo1",
            "test_pictures/photo_1_white_green_orange.jpg",
            "--photo2",
            "test_pictures/photo_2_yellow_blue_red.jpg",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Status: found" in captured.out


def test_capture_guide_reports_missing_photo_paths(capsys):
    exit_code = main(
        [
            "--capture-guide",
            "--photo1",
            "missing_photo_1.jpg",
            "--photo2",
            "missing_photo_2.jpg",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "warning: not found" in captured.out


def test_capture_guide_rejects_colors_input(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--capture-guide", "--colors", "w w w"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "only for instructions" in captured.err


def test_capture_guide_rejects_faces_input(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--capture-guide", "--faces", "--u", SOLVED_U_FACE])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "only for instructions" in captured.err


def test_capture_guide_rejects_facelet_input(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--capture-guide", SOLVED_FACELET_STATE])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "only for instructions" in captured.err
