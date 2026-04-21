# Test Pictures

This folder contains real cube photos for future image-processing tests.

The current program does not process these pictures yet.
These images are reference assets for the future two-picture workflow only.
Users can manually read these pictures and test the solver with `--faces`.
The program still does not detect sticker colors automatically.
Capture instructions are available with `python -m rubiks_solver.cli --capture-guide`.

Current sample picture paths:

- `test_pictures/photo_1_white_green_orange.jpg`
- `test_pictures/photo_2_yellow_blue_red.jpg`

Sample point templates:

- `test_pictures/sample_points_photo_1_template.json`
- `test_pictures/sample_points_photo_2_template.json`

You can copy these templates and adjust the `x` and `y` values to match the real sticker centers.
The sampler can write a JSON report and an optional annotated image:

```bash
python -m rubiks_solver.image_sampler --image test_pictures/photo_1_white_green_orange.jpg --points test_pictures/sample_points_photo_1_template.json --output reports/photo_1_samples.json --annotated-output reports/photo_1_samples_annotated.jpg
```

Current capture idea:

- Photo 1: white/up, green/front, orange/left
- Photo 2: yellow/down, blue/back, red/right

Things that may affect future color detection:

- Lighting
- Camera angle
- Blur
- Glare
- Red and orange looking too similar

These pictures should stay committed if they are small enough.
Do not put private or unrelated images in this folder.
