---
name: create-background
description: >-
  Creates 21:9 classic 1990s pixel art point-and-click adventure game background
  prompts and images from a scene description and style cue. Use this skill
  whenever the user asks to design, prompt, or generate a room, scene, or
  environment background for the pixel art adventure game.
---

# Create 21:9 Adventure Background

Follow this workflow to produce consistent, repeatable 21:9 classic pixel art adventure backgrounds across rooms and game zones.

## Workflow

1. **Gather Inputs**
   Identify two inputs from the user's request (ask briefly if missing or ambiguous):
   - **Scene Description**: Environment type, foreground framing elements, midground interactive/landmark props, background scenery, light sources, and time of day.
   - **Style Cue**: Either an existing zone's locked style cue or one selected/adapted from [references/style-cues.md](./references/style-cues.md).

2. **Assemble the Prompt**
   Load [resources/background-prompt.md](./resources/background-prompt.md) and fill in ONLY the two placeholders:
   - `[SCENE DESCRIPTION, including key props, lighting, and time of day]`
   - `[STYLE CUE]`
   Keep the `Composition`, `Technical aesthetic`, and `Constraints` lines **verbatim** so rooms share a cohesive visual language. Check [references/style-cues.md](./references/style-cues.md) for room-to-room scale and walkbox rules.

3. **Generate or Output**
   - **If the user wants the prompt text**: Return the assembled prompt cleanly.
   - **If the user wants a generated image**: Delegate to the `image-generator` subagent (or active image generation tool), passing:
     - The full assembled prompt verbatim
     - Explicit `21:9` ultrawide aspect ratio
     - Target output file path (e.g., under `creative/` or the user-specified folder)

4. **Validate the Result**
   Verify against these criteria before finishing:
   - **21:9 Framing**: Ultrawide theatrical stage framing without borders or letterboxing.
   - **Walkable Lower Third**: Clear, unobstructed floor path across the lower third for character navigation.
   - **Pixel Purity**: Crisp pixel clusters and deliberate dithering—no smooth gradients, blur, or painterly anti-aliasing.
   - **Clean Environment**: Zero characters, people, HUD/UI elements, verb bars, dialogue boxes, or text.
