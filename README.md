# Rubik's Cube Solver Algorithm

Python scaffold for solving a Rubik's Cube from either a manual 54-character cube state
string or a 54-sticker color-name state. Current version validates input, converts color
input or manual per-face input into the internal Kociemba facelet format, solves the cube
with the `kociemba` package, converts the solution into simple robot-friendly color and
angle commands, includes static debug tools, and now adds a live camera face scanner.

## What This Project Does Right Now

- Accepts a cube state string in standard Kociemba facelet order.
- Accepts a 54-sticker color input string with fast one-letter tokens or full color names and converts it into facelets.
- Accepts manual picture-assisted `--faces` input for one face at a time.
- Samples RGB and HSV values from manual image coordinates for debugging.
- Scans one face at a time from a live camera feed with a 3x3 overlay.
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
Manual `--faces` input is a bridge between real sample photos and future automatic image reading.
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

Solve a cube from 54 shorthand color tokens:

```bash
python -m rubiks_solver.cli --colors "w w w w w w w w w r r r r r r r r r g g g g g g g g g y y y y y y y y y o o o o o o o o o b b b b b b b b b"
```

Solve a cube from 54 full color names:

```bash
python -m rubiks_solver.cli --colors "white white white white white white white white white red red red red red red red red red green green green green green green green green green yellow yellow yellow yellow yellow yellow yellow yellow yellow orange orange orange orange orange orange orange orange orange blue blue blue blue blue blue blue blue blue"
```

Solve a cube from six manually read faces using current picture preset:

```bash
python -m rubiks_solver.cli --faces --u "y y g y w b r y w" --f "b g w g g w y r r" --l "o w r g o b b r o" --d "r b b w y w g y w" --b "y o o b b o y o o" --r "g r b o r g w r g"
```

Print the manual capture guide:

```bash
python -m rubiks_solver.cli --capture-guide
```

Print the manual capture guide with optional sample photo paths:

```bash
python -m rubiks_solver.cli --capture-guide --photo1 test_pictures/photo_1_white_green_orange.jpg --photo2 test_pictures/photo_2_yellow_blue_red.jpg
```

If the string is invalid, the CLI prints a simple error.
If the string describes an impossible cube, the CLI prints a simple error.
If both facelet input and `--colors` are provided, the CLI prints a simple error.
Full color names still work for compatibility.
`--capture-guide` only prints manual instructions. It does not process, open, or detect anything from images.

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

### Color Input

Color input uses the same sticker order as Kociemba facelets:

- First 9 stickers = Up face
- Next 9 stickers = Right face
- Next 9 stickers = Front face
- Next 9 stickers = Down face
- Next 9 stickers = Left face
- Last 9 stickers = Back face

Accepted color tokens:

- `white` or `w`
- `yellow` or `y`
- `green` or `g`
- `blue` or `b`
- `red` or `r`
- `orange` or `o`

Color input rules:

- Must contain exactly 54 color tokens.
- Tokens are separated by spaces.
- Input is case-insensitive.
- Each accepted color must appear exactly 9 times.
- One-letter shorthand is the main fast input format.

### Manual Face Input

`--faces` is manual picture-assisted input, not image processing.
You enter each face separately with `--u`, `--r`, `--f`, `--d`, `--l`, and `--b`.

Current real capture workflow uses default preset `capture-v1`.
It currently applies these face rotations before assembly:

- `U` = rotate counter-clockwise
- `R` = keep
- `F` = keep
- `D` = keep
- `L` = rotate counter-clockwise
- `B` = rotate 180

This matches the current sample photos:

- `U` = white face
- `F` = green face
- `L` = orange face
- `D` = yellow face
- `B` = blue face
- `R` = red face

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

## Future Capture Contract

Two-picture design contract lives in [docs/two_picture_capture_contract.md](docs/two_picture_capture_contract.md).
It describes the first proposed photo workflow for future image detection.
Sample test pictures can be stored in [test_pictures/](test_pictures/).
Current real sample set uses `photo_1_white_green_orange.jpg` and `photo_2_yellow_blue_red.jpg`.
The project still does not process images automatically yet.
Folder notes live in [test_pictures/README.md](test_pictures/README.md).
Manual capture instructions are available from `python -m rubiks_solver.cli --capture-guide`.

## Image Sampling Debug

First image-debug tool lives in `python -m rubiks_solver.image_sampler`.
It samples manually provided pixel coordinates from an image and writes a JSON report with RGB and HSV values.
It does not detect stickers automatically and it does not solve from images yet.
This helps inspect lighting, color separation, and red/orange differences before future detection work.

User-assisted point picker lives in `python -m rubiks_solver.point_picker`.
It opens an image, lets you click sticker centers, and saves a real sample-points JSON file.
This is still user-assisted, not automatic detection.
The picker now records both:

- `face_color`: the home color of the face being labeled
- `sticker_color`: the actual sticker color chosen by the user while clicking

This gives ground-truth labels for future color classification work.

Photo 1 picker:

```bash
python -m rubiks_solver.point_picker --image test_pictures/photo_1_white_green_orange.jpg --image-role photo_1 --output test_pictures/sample_points_photo_1.json
```

Photo 2 picker:

```bash
python -m rubiks_solver.point_picker --image test_pictures/photo_2_yellow_blue_red.jpg --image-role photo_2 --output test_pictures/sample_points_photo_2.json
```

Example command:

```bash
python -m rubiks_solver.image_sampler --image test_pictures/photo_1_white_green_orange.jpg --points test_pictures/sample_points_photo_1_template.json --output reports/photo_1_samples.json --annotated-output reports/photo_1_samples_annotated.jpg
```

Use the generated point file with the sampler:

```bash
python -m rubiks_solver.image_sampler --image test_pictures/photo_1_white_green_orange.jpg --points test_pictures/sample_points_photo_1.json --output reports/photo_1_samples.json
```

Template point files live in:

- `test_pictures/sample_points_photo_1_template.json`
- `test_pictures/sample_points_photo_2_template.json`

## Live Face Scanner

Camera-first debug tool lives in `python -m rubiks_solver.live_face_scanner`.
It reads one face at a time from a live webcam feed.
The user aligns one cube face inside a 3x3 overlay.
The scanner samples the 8 surrounding stickers plus the center sticker.
The center sticker is especially important because it identifies the face color.
The color classifier is experimental and easy to tune later.
It does not solve the full cube from camera yet.

Example commands:

```bash
python -m rubiks_solver.live_face_scanner --camera 0
```

```bash
python -m rubiks_solver.live_face_scanner --camera 0 --face U --output captures/u_face_scan.json
```

## Project Structure

```text
docs/
  two_picture_capture_contract.md
rubiks_solver/
  __init__.py
  capture_guide.py
  color_state.py
  cli.py
  face_input.py
  image_sampler.py
  image_sampling.py
  live_face_scanner.py
  point_picker.py
  robot_moves.py
  solver.py
  validation.py
tests/
  test_cli.py
  test_color_state.py
  test_face_input.py
  test_image_sampling.py
  test_live_face_scanner.py
  test_point_picker.py
  test_robot_moves.py
  test_solver.py
  test_validation.py
test_pictures/
  README.md
  photo_1_white_green_orange.jpg
  photo_2_yellow_blue_red.jpg
  sample_points_photo_1_template.json
  sample_points_photo_2_template.json
requirements.txt
README.md
```
