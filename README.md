# Rubik's Cube Solver Algorithm

Python scaffold for solving a Rubik's Cube from either a manual 54-character cube state
string or a 54-sticker color-name state. Current version validates input, converts color
input into the internal Kociemba facelet format, solves the cube with the `kociemba`
package, and converts the solution into simple robot-friendly color and angle commands.

## What This Project Does Right Now

- Accepts a cube state string in standard Kociemba facelet order.
- Accepts a 54-sticker color-name input string and converts it into facelets.
- Validates basic input rules before solving.
- Solves the cube with the `kociemba` Python package.
- Prints standard Rubik's Cube notation such as `R U R' U'`.
- Prints robot-friendly commands such as `red, 90` and `white, -90`.

Robot-friendly output currently means:

- Colored face plus angle only.
- No motor control yet.
- `90` means clockwise.
- `-90` means counter-clockwise.
- `180` means half turn.
- Clockwise and counter-clockwise are defined from the viewpoint of looking directly at that face.

## What This Project Does Not Do Yet

- It does not do image capture or image processing yet.
- It does not read two pictures of the cube yet.
- It does not control a robot yet.
- It does not convert face turns into hardware or motor commands yet.
- It does not auto-detect the cube orientation yet.

Image capture from 2 pictures with 3 visible faces per picture is planned for a later step.
Color-name input is a bridge toward that future image-detection step.
The motor-control layer will come later after the robot mechanism is known.

## Install

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Show CLI help:

```bash
python -m rubiks_solver.cli --help
```

Solve a cube from a 54-character facelet state string:

```bash
python -m rubiks_solver.cli UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
```

Solve a cube from 54 color names:

```bash
python -m rubiks_solver.cli --colors "white white white white white white white white white red red red red red red red red red green green green green green green green green green yellow yellow yellow yellow yellow yellow yellow yellow yellow orange orange orange orange orange orange orange orange orange blue blue blue blue blue blue blue blue blue"
```

If the string is invalid, the CLI prints a simple error.
If the string describes an impossible cube, the CLI prints a simple error.
If both facelet input and `--colors` are provided, the CLI prints a simple error.

## Input Formats

### Facelet Input

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

### Color-Name Input

Color-name input uses the same sticker order as Kociemba facelets:

- First 9 stickers = Up face
- Next 9 stickers = Right face
- Next 9 stickers = Front face
- Next 9 stickers = Down face
- Next 9 stickers = Left face
- Last 9 stickers = Back face

Accepted color names:

- `white`
- `yellow`
- `green`
- `blue`
- `red`
- `orange`

Color input rules:

- Must contain exactly 54 color names.
- Colors are separated by spaces.
- Input is case-insensitive.
- Each accepted color must appear exactly 9 times.

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
- `F = green`
- `B = blue`
- `R = red`
- `L = orange`

Current confirmed orientation:

- `white = Up` is confirmed.
- `yellow = Down` is confirmed.
- `green = Front` is confirmed.

Current default full mapping:

- `U = white`
- `D = yellow`
- `F = green`
- `B = blue`
- `R = red`
- `L = orange`

Only white, yellow, and green are confirmed right now.
Blue, red, and orange stay as easy-to-edit defaults until the real robot and cube orientation are finalized.

## Project Structure

```text
rubiks_solver/
  __init__.py
  color_state.py
  cli.py
  robot_moves.py
  solver.py
  validation.py
tests/
  test_cli.py
  test_color_state.py
  test_robot_moves.py
  test_solver.py
  test_validation.py
requirements.txt
README.md
```
