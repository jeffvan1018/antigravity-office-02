# Style Cues & Multi-Room Consistency Guide

## Preset `[STYLE CUE]` Options

- **LucasArts Golden Era (Monkey Island / Day of the Tentacle)**
  ```text
  Early 90s LucasArts VGA 256-color aesthetic, expressive slightly whimsical proportions, rich painterly pixel shading, warm theatrical lighting
  ```

- **Sierra Sci-Fi / Moody (Space Quest / Beneath a Steel Sky)**
  ```text
  1992 VGA sci-fi adventure aesthetic, gritty industrial textures, high-contrast shadow dithering, cool cyan and amber accent lighting
  ```

- **Neo-Retro / 32-Bit Adventure (Thimbleweed Park)**
  ```text
  Clean 32-bit era crisp pixel art, moody atmospheric lighting shafts, rich moody color grading, intricate pixel clutter
  ```

- **EGA Retro (Loom / Early Sierra)**
  ```text
  1989 16-color EGA pixel art aesthetic, heavy checkerboard and crosshatch dithering, bold graphic silhouettes
  ```

---

## Scene Description Best Practices

Structure `[SCENE DESCRIPTION]` with three depth planes in mind:
1. **Foreground framing** (edges/corners only, never blocking the walkbox): e.g., overhanging cables, doorframes, shadowed pillars, potted plants at screen edges.
2. **Midground props** (above the walkable floor): desks, machines, doorways, terminals, counters, signage shapes (without readable text).
3. **Background atmosphere**: windows, skyline, distant corridors, lighting shafts, time-of-day cues.

*Example:*
`Interior wide room view of a cluttered late-night tech startup bullpen, shadowed server rack edges framing the far left and right foreground, rows of glowing green CRT monitors on desks and a flickering vending machine in the midground, rain-streaked glass windows overlooking a dark city skyline in the background, warm desk lamps casting pools of light.`

---

## Consistency Rules Across Rooms

1. **Lock Zone Style Cues:** Once a `[STYLE CUE]` is chosen for a game zone or act, copy it character-for-character across every room in that zone.
2. **Pass Native 21:9 Aspect Ratio:** Always set native `21:9` aspect ratio parameters in the image tool in addition to keeping `21:9` in the prompt text.
3. **Keep Camera Distance Consistent:** Explicitly anchor camera scale in `Scene:` (e.g., `Interior wide room view of...` or `Street-level exterior wide view of...`) so character sprites remain proportional across room transitions.
4. **Protect the Walkbox:** Keep large furniture and obstacles out of the center-bottom lower third so characters have a natural horizontal path.
