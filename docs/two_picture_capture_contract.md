# Two-Picture Capture Contract

## Purpose

This document defines how two photos should be taken so future image processing can map
detected colors into the correct 54-sticker cube order.

This is a design contract only.
No image processing is implemented yet.
This two-photo plan is provisional and may change after more testing.

Real sample photos now live under `test_pictures/`.
They are reference assets for manual inspection and future image-processing development.
The project still does not automatically read these images yet.
Manual face input is now implemented for users who want to read these photos by hand.
A capture guide CLI now exists to help users manually read the current sample photos.
Automatic image processing is still not implemented.
Image sampling debug now exists with manual coordinate JSON files.
It is meant to help tune future color detection, not replace it.

## Current Confirmed Orientation

- White = Up
- Yellow = Down
- Green = Front

## Current Assumed Full Cube Orientation

- U = white
- D = yellow
- F = green
- B = blue
- R = red
- L = orange

## Proposed Two-Photo Capture Plan

This is the first proposed capture contract.
It may be revised after testing with real pictures.

Current real sample photos show orange in Photo 1 and red in Photo 2.
Because of that, the current contract is now based on:

- Photo 1: `U / F / L`
- Photo 2: `D / B / R`

| Photo | Visible faces | Purpose |
|---|---|---|
| Photo 1 | U / F / L | Captures white, green, orange |
| Photo 2 | D / B / R | Captures yellow, blue, red |

### Photo 1

- Cube held with white face on top.
- Green face looking toward the camera/front.
- Visible faces:
  - Up / white
  - Front / green
  - Left / orange

### Photo 2

- Cube rotated so yellow face is visible.
- Keep the same cube orientation logic as much as possible.
- Visible faces should complete the missing faces:
  - Down / yellow
  - Back / blue
  - Right / red

Important challenge:

- Preserving face orientation and sticker ordering between photos is still the hard part.

## Manual Face Input Preset

Current CLI supports manual per-face entry with `--faces`.
Automatic image reading is still not implemented.

Current preset name:

- `capture-v1`

`capture-v1` currently applies these face rotations before assembly:

- `U` = rotate counter-clockwise
- `R` = keep
- `F` = keep
- `D` = keep
- `L` = rotate counter-clockwise
- `B` = rotate 180

These rotation rules were based on the current real sample photos and may change after more tests.

## Sticker Indexing Inside Each Face

Every face should use this 3x3 sticker index order:

```text
0 1 2
3 4 5
6 7 8
```

Each face must eventually be stored in that order.

The full 54-sticker order must match Kociemba:

```text
U0 U1 U2 U3 U4 U5 U6 U7 U8
R0 R1 R2 R3 R4 R5 R6 R7 R8
F0 F1 F2 F3 F4 F5 F6 F7 F8
D0 D1 D2 D3 D4 D5 D6 D7 D8
L0 L1 L2 L3 L4 L5 L6 L7 L8
B0 B1 B2 B3 B4 B5 B6 B7 B8
```

## Future Image Pipeline

- Use image sampling debug reports to inspect RGB and HSV values from real stickers.
- Load two images.
- Detect or manually select the 3 visible faces in each image.
- Sample 9 stickers per face.
- Classify each sticker into one of the six colors.
- Assemble colors into the 54-sticker Kociemba order.
- Convert color tokens to facelets.
- Solve.
- Output color + angle commands.

## Open Questions And Risks

- How exactly the cube will be physically rotated between photo 1 and photo 2.
- Whether sticker orientation on back, left, and down faces needs extra rotation correction.
- Whether image detection will be automatic or user-assisted at first.
- Lighting and color calibration.
- Whether the robot will need a different internal orientation than the human-readable solver output.
