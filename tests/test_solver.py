from rubiks_solver.solver import solve_cube


SOLVED_CUBE = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"


def test_solve_cube_returns_empty_solution_for_solved_cube():
    assert solve_cube(SOLVED_CUBE) == ""
