# Object Sprite Scale, Perspective & Style Guide

## 1. Matching Room Style & Perspective

- **Reuse Zone Style Cues**: Copy the room's `[STYLE CUE]` verbatim from [../create-background/references/style-cues.md](../create-background/references/style-cues.md) (e.g., *LucasArts Golden Era*, *Sierra Sci-Fi / Moody*, *Neo-Retro / 32-Bit Adventure*, or *EGA Retro*).
- **Inspect Target Background First**: When creating an object for an existing room in `creative/backgrounds/`, inspect that background file to match:
  - **Pixel dimensions** (standard `21:9` backgrounds are `1376×590`; some existing room variants are `1376×768`).
  - **Lighting direction & color temperature** (e.g., warm window sunlight from the right vs. cool overhead fluorescent strips).
  - **Camera angle**: Slightly elevated eye-level 2D stage view (subtle top surfaces visible on floor/tabletop items; straight-on or wall-aligned perspective for wall-mounted posters, clocks, or signs; never steep 45° isometric top-down).

---

## 2. Background-Relative Sprite Scale Table (Midground `1.0×` Baseline)

Size sprites relative to the room background's height (`H`) so they drop onto the background at **1:1 scale without manual resizing**.

*(Calibration anchors: On a `1376×590` room background, a standing character in the midground walkbox is `~224 px` (`0.38 H`) and a standard interior doorway is `~248 px` (`0.42 H`).)*

| Size Tier | Typical Midground Objects | `--height-ratio` (`% of H`) | Target Height @ `1376×590` | Target Height @ `1376×768` |
| :--- | :--- | :--- | :--- | :--- |
| **Tiny / Handheld** | Coffee mug, stapler, ID badge/keycard, soda can, mouse, phone, book stack | `0.04 – 0.07` | `24 – 42 px` | `31 – 54 px` |
| **Small Tabletop / Floor Prop** | CRT monitor, desk lamp, PC tower, microwave, backpack, trash bin, small potted plant, fire extinguisher | `0.08 – 0.14` | `48 – 82 px` | `62 – 108 px` |
| **Medium Furniture** | Office desk, rolling task chair, filing cabinet, water cooler, printer/copier, beanbag, low cabinet | `0.17 – 0.25` | `100 – 148 px` | `130 – 192 px` |
| **Large / Full-Height Prop** | Vending machine, server rack, cubicle partition, tall bookcase, arcade cabinet, indoor tree, fridge | `0.34 – 0.44` | `200 – 260 px` | `260 – 338 px` |

### Depth Plane Multipliers
Adjust the midground baseline when the user specifies where in the room the object will sit:
- **Foreground** (near bottom screen edge / framing): **`1.25× – 1.40×`** midground size.
- **Midground** (standard interactive room stage — default): **`1.00×`**.
- **Far Midground / Background** (back wall or distant corridor): **`0.65× – 0.80×`** midground size.

### Wide / Flat Horizontal Objects (`--target-width` or `--width-ratio`)
For flat or wide horizontal props (area rugs, floor cables, keyboards, wide tables, couches, wall banners), anchor by **width** against background width (`W = 1376`) instead of height so flat silhouettes stay proportional:
- **Small flat item** (keyboard, laptop, pizza box): `--target-width 48` to `75` (`--width-ratio 0.035` to `0.055`)
- **Standard workstation / desk**: `--target-width 165` to `230` (`--width-ratio 0.12` to `0.17`)
- **Wide sofa / conference table / rug**: `--target-width 250` to `360` (`--width-ratio 0.18` to `0.26`)

---

## 3. Detail Density & Chroma-Key Selection

- **Detail Density for Small Sprites**: When final height is under `75 px`, add *"bold chunky readable pixel clusters and simplified iconic details"* inside `[OBJECT DESCRIPTION]` so nearest-neighbor downscaling stays crisp and legible.
- **Chroma-Key Backdrop Color (`[CHROMA KEY COLOR]`)**:
  - **Default**: `#FF00FF pure magenta`
  - **If the object has pink, magenta, purple, or red-violet hues**: `#00FF00 pure lime green`
  - **If the object has both magenta/pink AND bright green hues**: `#00FFFF pure cyan`
- **Generator Aspect Ratio**:
  - Default `1:1` square for standard props.
  - `16:9` for wide horizontal props (long tables, couches, banners, rugs).
  - `9:16` for tall narrow props (floor lamps, server racks, vending machines, trees).
