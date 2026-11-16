---
name: create-object-sprite
description: >-
  Creates transparent-background classic 1990s pixel art adventure game object
  sprites pre-sized to match 21:9 room backgrounds at 1:1 scale, outputting
  only the final sprite in creative/objects/ with no interim files. Use this
  skill whenever the user asks to design, generate, or create an interactive
  object, prop, furniture piece, or item sprite for the pixel art adventure game.
---

# Create Adventure Object Sprite

Follow this workflow to generate clean, transparent-background pixel art object sprites in `creative/objects/` that match rooms created with `create-background` at 1:1 pixel scale—without leaving interim files behind.

## Workflow

1. **Gather Inputs & Calibrate Scale**
   Identify from the user's request (ask briefly only if genuinely ambiguous):
   - **Object Description**: Prop type, facing/orientation, state (e.g., open/closed, powered on), surface materials, and lighting direction.
   - **Target Room / Style Cue**:
     - If matching an existing room in `creative/backgrounds/`, inspect that background image (`read_file`) to match its lighting direction, perspective, pixel dimensions, and zone style.
     - Otherwise, select/adapt a `[STYLE CUE]` from [../create-background/references/style-cues.md](../create-background/references/style-cues.md) and assume the standard `1376×590` (`21:9`) room dimensions.
   - **Target Pixel Dimensions**: Use [references/scale-and-style.md](./references/scale-and-style.md) to pick the exact `--target-height` (or `--target-width` for flat/wide objects, or `--reference-bg` + `--height-ratio` / `--width-ratio`) so the sprite drops into the scene with zero manual scaling.

2. **Assemble the Prompt**
   Load [resources/object-sprite-prompt.md](./resources/object-sprite-prompt.md) and fill in ONLY the three placeholders:
   - `[OBJECT DESCRIPTION, including orientation, surface materials, state, and lighting direction]` (for small sprites `< 75 px`, include *"bold chunky readable pixel clusters and simplified iconic details"*)
   - `[STYLE CUE]`
   - `[CHROMA KEY COLOR]`: Use `#FF00FF pure magenta` by default; switch to `#00FF00 pure lime green` if the object contains pink, magenta, purple, or red-violet tones (or `#00FFFF pure cyan` if both).
   Keep `Composition`, `Backdrop`, `Technical aesthetic`, and `Constraints` **verbatim**.

3. **Generate & Post-Process In-Place (No Interim Files)**
   - **Output Path**: Save under `creative/objects/` instead of `creative/backgrounds/` (e.g., `creative/objects/<object-name>.png` or `creative/objects/<zone>/<object-name>.png` to mirror a room zone like `cube-farm`, unless the user specifies an exact path).
   - **Zero Interim Files Rule**: Never save `-raw`, `-chroma`, `-cropped`, `-preview`, or composite comparison images anywhere in the workspace. Only the single requested sprite file may exist when finished.
   - **If the user wants only the prompt text**: Return the assembled prompt cleanly without generating files.
   - **Generate & Convert**:
     1. Delegate to the `image-generator` subagent with the verbatim prompt, appropriate aspect ratio (`1:1` default, `16:9` for wide props, `9:16` for tall narrow props), and instruct it to write **only** the single image directly to the final output path in `creative/objects/`.
     2. Immediately run [scripts/process_sprite.py](./scripts/process_sprite.py) **in-place** on that exact output file to strip the chroma-key background (including enclosed holes and edge spill), crop tightly to the non-transparent bounds, and resize with crisp `NEAREST` resampling to the background-matched pixel dimensions:
        ```bash
        python3 creative/skills/create-object-sprite/scripts/process_sprite.py \
          creative/objects/<path-to-sprite>.png \
          --target-height <PX>
        ```
        *(Alternatively pass `--reference-bg creative/backgrounds/<zone>/<room>.png --height-ratio <RATIO>` or `--target-width <PX>`. If `image-generator` saved to any path other than the final destination, pass `--output <final-path> --delete-input` so the raw file is immediately removed.)*

4. **Validate the Result**
   Inspect the JSON output from `process_sprite.py` and view the final PNG with `read_file`:
   - **True RGBA Transparency**: Background and enclosed cutouts have `alpha = 0`, with no baked checkerboard and no magenta/green fringe halo along outlines.
   - **1:1 Background Scale**: Final pixel dimensions match the room's perspective and size tier from [references/scale-and-style.md](./references/scale-and-style.md).
   - **Pixel Purity**: Sharp nearest-neighbor pixel clusters, binary alpha (`0` or `255`), and zero anti-aliased blur.
   - **Single Output Only**: Verify `creative/objects/` contains only the requested sprite and zero interim files.
