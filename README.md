# Rubik's Cube Solver Algorithm

Python scaffold for solving a Rubik's Cube from a manual 54-character cube state string.
Current version validates a cube state, solves it with the `kociemba` package, and converts
the solution into simple robot-friendly color and angle commands.

## What This Project Does Right Now

- Accepts a cube state string in standard Kociemba facelet order.
- Validates basic input rules before solving.
- Solves the cube with the `kociemba` Python package.
- Prints standard Rubik's Cube notation such as `R U R' U'`.
- Prints robot-friendly commands such as `red, 90` and `white, -90`.

## What This Project Does Not Do Yet

- It does not do image capture or image processing yet.
- It does not read two pictures of the cube yet.
- It does not control a robot yet.
- It does not auto-detect the cube orientation yet.

Image capture from 2 pictures with 3 visible faces per picture is planned for a later step.

## Install

1. Create and activate a Python virtual environment if you want one.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Show CLI help:

```bash
python -m rubiks_solver.cli --help
```

Solve a cube from a 54-character state string:

```bash
python -m rubiks_solver.cli UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

If the string is invalid, the CLI prints a simple error.
If the string describes an impossible cube, the CLI prints a simple error.

## Cube State Format

Use the standard Kociemba facelet order:

```text
UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

Face meaning:

- `U` = Up
- `R` = Right
- `F` = Front
- `D` = Down
- `L` = Left
- `B` = Back

The string must:

- Be exactly 54 characters long.
- Use only the letters `U`, `R`, `F`, `D`, `L`, and `B`.
- Contain each face letter exactly 9 times.

## Example Output

Example normal solver output:

```text
R U R' U'
```

Example robot-friendly output:

```text
red, 90
white, 90
red, -90
white, -90
```

For a solved cube, the solver prints that the cube is already solved and that no robot moves are needed.

## Face Color Mapping

Current editable default mapping in code:

- `U = white`
- `D = yellow`
- `R = red`
- `L = orange`
- `F = green`
- `B = blue`

Important note:

- `white = Up` is confirmed.
- `yellow = Down` is confirmed.
- `red`, `orange`, `green`, and `blue` are temporary defaults for now and can be changed later to match the real robot and cube orientation.

## Project Structure

```text
rubiks_solver/
  __init__.py
  cli.py
  robot_moves.py
  solver.py
  validation.py
tests/
  test_robot_moves.py
  test_validation.py
requirements.txt
README.md
```
