# Two-Picture Capture Contract

## Purpose

This document defines how two photos should be taken so future image processing can map
detected colors into the correct 54-sticker cube order.

This is a design contract only.
No image processing is implemented yet.

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

### Photo 1

- Cube held with white face on top.
- Green face looking toward the camera/front.
- Visible faces:
- Up / white
- Front / green
- Right / red

### Photo 2

- Cube rotated so yellow face is visible.
- Keep the same cube orientation logic as much as possible.
- Visible faces should complete the missing faces:
- Down / yellow
- Back / blue
- Left / orange

Important challenge:

- Hardest part is preserving face orientation and sticker ordering between photos.

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
