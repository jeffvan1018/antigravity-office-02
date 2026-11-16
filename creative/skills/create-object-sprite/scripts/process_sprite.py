#!/usr/bin/env python3
"""Post-process a generated pixel-art object sprite in-place (or to --output).

Removes solid chroma-key backgrounds (including enclosed interior holes and
anti-aliased color spill/halos), crops tightly to the non-transparent bounds,
and resizes with crisp nearest-neighbor resampling to match the room background
at 1:1 scale without leaving any interim files on disk.
"""

from __future__ import annotations

import argparse
from collections import deque
import io
import json
from pathlib import Path
import sys
from PIL import Image


def parse_hex_or_named_color(spec: str) -> tuple[int, int, int] | None:
    s = spec.strip().lower()
    if s == "auto":
        return None
    named = {
        "magenta": (255, 0, 255),
        "green": (0, 255, 0),
        "cyan": (0, 255, 255),
    }
    if s in named:
        return named[s]
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    raise ValueError(f"Unsupported --key-color value: {spec!r}")


def detect_border_key_color(
    rgba: bytes, width: int, height: int
) -> tuple[int, int, int]:
    """Detect the dominant solid background color along the outer 2px border."""
    buckets: dict[tuple[int, int, int], list[tuple[int, int, int]]] = {}
    border_thick = min(2, width // 2, height // 2) or 1

    def add_pixel(x: int, y: int) -> None:
        idx = (y * width + x) * 4
        r, g, b, a = rgba[idx], rgba[idx + 1], rgba[idx + 2], rgba[idx + 3]
        if a < 128:
            return
        q = (r >> 3, g >> 3, b >> 3)
        buckets.setdefault(q, []).append((r, g, b))

    for y in range(height):
        for x in (
            list(range(border_thick)) + list(range(max(border_thick, width - border_thick), width))
            if border_thick <= y < height - border_thick
            else range(width)
        ):
            add_pixel(x, y)

    if not buckets:
        return (255, 0, 255)

    dominant = max(buckets.values(), key=len)
    n = len(dominant)
    return (
        round(sum(p[0] for p in dominant) / n),
        round(sum(p[1] for p in dominant) / n),
        round(sum(p[2] for p in dominant) / n),
    )


def classify_chroma_mode(kr: int, kg: int, kb: int) -> str:
    if kr >= 165 and kb >= 165 and kg <= 110 and min(kr, kb) - kg >= 80:
        return "magenta"
    if kg >= 165 and kr <= 110 and kb <= 110 and kg - max(kr, kb) >= 80:
        return "green"
    if kg >= 165 and kb >= 165 and kr <= 110 and min(kg, kb) - kr >= 80:
        return "cyan"
    return "generic"


def chroma_dominance(r: int, g: int, b: int, mode: str) -> int:
    if mode == "magenta":
        return min(r, b) - g
    if mode == "green":
        return g - max(r, b)
    if mode == "cyan":
        return min(g, b) - r
    return 0


def despill_pixel(r: int, g: int, b: int, mode: str) -> tuple[int, int, int]:
    """Clamp residual chroma channel bleed on thin 1-2px features."""
    if mode == "magenta":
        excess = min(r, b) - g
        if excess > 0:
            r = max(0, r - excess)
            b = max(0, b - excess)
    elif mode == "green":
        limit = max(r, b)
        if g > limit:
            g = limit
    elif mode == "cyan":
        excess = min(g, b) - r
        if excess > 0:
            g = max(0, g - excess)
            b = max(0, b - excess)
    return (r, g, b)


def border_already_transparent(rgba: bytes, width: int, height: int) -> bool:
    total = 0
    transparent = 0
    for x in range(width):
        for y in (0, height - 1):
            total += 1
            if rgba[(y * width + x) * 4 + 3] < 32:
                transparent += 1
    for y in range(1, height - 1):
        for x in (0, width - 1):
            total += 1
            if rgba[(y * width + x) * 4 + 3] < 32:
                transparent += 1
    return total > 0 and (transparent / total) > 0.6


def remove_background(
    im: Image.Image,
    key_spec: str = "auto",
    tolerance: int = 65,
) -> tuple[Image.Image, dict[str, object]]:
    im_rgba = im.convert("RGBA")
    width, height = im_rgba.size
    buf = bytearray(im_rgba.tobytes())
    n_pixels = width * height

    if key_spec == "auto" and border_already_transparent(buf, width, height):
        # Clean binary alpha for crisp pixel art
        for i in range(n_pixels):
            idx = i * 4
            if buf[idx + 3] < 128:
                buf[idx] = 0
                buf[idx + 1] = 0
                buf[idx + 2] = 0
                buf[idx + 3] = 0
            else:
                buf[idx + 3] = 255
        out = Image.frombytes("RGBA", (width, height), bytes(buf))
        transparent_count = sum(1 for i in range(n_pixels) if buf[i * 4 + 3] == 0)
        return out, {
            "mode": "existing_alpha",
            "key_color": None,
            "transparent_pct": round(100.0 * transparent_count / max(1, n_pixels), 2),
        }

    explicit_key = parse_hex_or_named_color(key_spec)
    sampled_key = detect_border_key_color(buf, width, height)
    if explicit_key is None:
        kr, kg, kb = sampled_key
    else:
        # If border matches explicit key reasonably closely, anchor to actual rendered border shade
        d2_explicit = (
            (sampled_key[0] - explicit_key[0]) ** 2
            + (sampled_key[1] - explicit_key[1]) ** 2
            + (sampled_key[2] - explicit_key[2]) ** 2
        )
        kr, kg, kb = sampled_key if d2_explicit <= 80 * 80 else explicit_key

    mode = classify_chroma_mode(kr, kg, kb)

    bg_mask = bytearray(n_pixels)  # 1 = transparent background, 0 = foreground
    tol_sq = tolerance * tolerance
    seed_tol_sq = int((tolerance * 1.35) ** 2)

    def dist_sq_at(i: int) -> int:
        idx = i * 4
        dr = buf[idx] - kr
        dg = buf[idx + 1] - kg
        db = buf[idx + 2] - kb
        return dr * dr + dg * dg + db * db

    # 1. Exterior flood-fill from image border
    q: deque[int] = deque()
    for x in range(width):
        for y in (0, height - 1):
            i = y * width + x
            if not bg_mask[i] and (buf[i * 4 + 3] < 128 or dist_sq_at(i) <= seed_tol_sq):
                bg_mask[i] = 1
                q.append(i)
    for y in range(1, height - 1):
        for x in (0, width - 1):
            i = y * width + x
            if not bg_mask[i] and (buf[i * 4 + 3] < 128 or dist_sq_at(i) <= seed_tol_sq):
                bg_mask[i] = 1
                q.append(i)

    while q:
        cur = q.popleft()
        cx = cur % width
        cy = cur // width
        if cx > 0:
            nb = cur - 1
            if not bg_mask[nb] and dist_sq_at(nb) <= tol_sq:
                bg_mask[nb] = 1
                q.append(nb)
        if cx + 1 < width:
            nb = cur + 1
            if not bg_mask[nb] and dist_sq_at(nb) <= tol_sq:
                bg_mask[nb] = 1
                q.append(nb)
        if cy > 0:
            nb = cur - width
            if not bg_mask[nb] and dist_sq_at(nb) <= tol_sq:
                bg_mask[nb] = 1
                q.append(nb)
        if cy + 1 < height:
            nb = cur + width
            if not bg_mask[nb] and dist_sq_at(nb) <= tol_sq:
                bg_mask[nb] = 1
                q.append(nb)

    # 2. Punch out enclosed interior chroma-key holes (e.g. mug handles, chair legs)
    inner_seed_sq = int((tolerance * 0.65) ** 2)
    inner_fill_sq = int((tolerance * 0.92) ** 2)
    for i in range(n_pixels):
        if bg_mask[i]:
            continue
        idx = i * 4
        r, g, b = buf[idx], buf[idx + 1], buf[idx + 2]
        if dist_sq_at(i) <= inner_seed_sq and (
            mode == "generic" or chroma_dominance(r, g, b, mode) >= 110
        ):
            bg_mask[i] = 1
            q.append(i)
            while q:
                cur = q.popleft()
                cx = cur % width
                cy = cur // width
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        nb = ny * width + nx
                        if not bg_mask[nb] and dist_sq_at(nb) <= inner_fill_sq:
                            bg_mask[nb] = 1
                            q.append(nb)

    # 3. Erode 1px heavily key-blended anti-aliased outer fringe
    fringe_tol_sq = int((tolerance * 1.55) ** 2)
    to_erode: list[int] = []
    for y in range(height):
        row = y * width
        for x in range(width):
            i = row + x
            if bg_mask[i]:
                continue
            # Check if adjacent to background
            adj_bg = (
                (x > 0 and bg_mask[i - 1])
                or (x + 1 < width and bg_mask[i + 1])
                or (y > 0 and bg_mask[i - width])
                or (y + 1 < height and bg_mask[i + width])
            )
            if not adj_bg:
                continue
            idx = i * 4
            r, g, b = buf[idx], buf[idx + 1], buf[idx + 2]
            dom = chroma_dominance(r, g, b, mode)
            if dist_sq_at(i) <= fringe_tol_sq or (mode != "generic" and dom >= 95):
                to_erode.append(i)
    for i in to_erode:
        bg_mask[i] = 1

    # 4. Compute distance from background up to 3px to identify clean interior palette pixels
    dist_from_bg = bytearray([255]) * n_pixels
    dq: deque[int] = deque()
    for i in range(n_pixels):
        if bg_mask[i]:
            dist_from_bg[i] = 0
            dq.append(i)

    while dq:
        cur = dq.popleft()
        d = dist_from_bg[cur]
        if d >= 4:
            continue
        cx = cur % width
        cy = cur // width
        nd = d + 1
        if cx > 0 and dist_from_bg[cur - 1] > nd:
            dist_from_bg[cur - 1] = nd
            dq.append(cur - 1)
        if cx + 1 < width and dist_from_bg[cur + 1] > nd:
            dist_from_bg[cur + 1] = nd
            dq.append(cur + 1)
        if cy > 0 and dist_from_bg[cur - width] > nd:
            dist_from_bg[cur - width] = nd
            dq.append(cur - width)
        if cy + 1 < height and dist_from_bg[cur + width] > nd:
            dist_from_bg[cur + width] = nd
            dq.append(cur + width)

    # 5. Decontaminate 1-2px boundary pixels with residual chroma spill by snapping
    #    to the nearest clean interior pixel (or clamping spill on thin 1-2px lines).
    if mode != "generic":
        updates: list[tuple[int, int, int, int]] = []
        offsets = [
            (dx, dy, dx * dx + dy * dy)
            for dy in range(-4, 5)
            for dx in range(-4, 5)
            if not (dx == 0 and dy == 0) and dx * dx + dy * dy <= 16
        ]
        offsets.sort(key=lambda t: t[2])

        for y in range(height):
            row = y * width
            for x in range(width):
                i = row + x
                d = dist_from_bg[i]
                if d == 0 or d > 2:
                    continue
                idx = i * 4
                r, g, b = buf[idx], buf[idx + 1], buf[idx + 2]
                dom = chroma_dominance(r, g, b, mode)
                if dom < 22:
                    continue
                snapped = None
                for dx, dy, _ in offsets:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        ni = ny * width + nx
                        if dist_from_bg[ni] >= 3:
                            nidx = ni * 4
                            nr, ng, nb = buf[nidx], buf[nidx + 1], buf[nidx + 2]
                            if chroma_dominance(nr, ng, nb, mode) < 18:
                                snapped = (nr, ng, nb)
                                break
                if snapped is None:
                    snapped = despill_pixel(r, g, b, mode)
                updates.append((idx, snapped[0], snapped[1], snapped[2]))

        for idx, nr, ng, nb in updates:
            buf[idx] = nr
            buf[idx + 1] = ng
            buf[idx + 2] = nb

    # 6. Strip tiny isolated floating dust specks away from the main sprite
    visited = bytearray(n_pixels)
    components: list[tuple[list[int], tuple[int, int, int, int]]] = []
    for i in range(n_pixels):
        if bg_mask[i] or visited[i]:
            continue
        visited[i] = 1
        comp = [i]
        cq = deque([i])
        min_x = max_x = i % width
        min_y = max_y = i // width
        while cq:
            cur = cq.popleft()
            cx = cur % width
            cy = cur // width
            if cx < min_x:
                min_x = cx
            if cx > max_x:
                max_x = cx
            if cy < min_y:
                min_y = cy
            if cy > max_y:
                max_y = cy
            for dy in (-1, 0, 1):
                ny = cy + dy
                if ny < 0 or ny >= height:
                    continue
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = cx + dx
                    if 0 <= nx < width:
                        nb = ny * width + nx
                        if not bg_mask[nb] and not visited[nb]:
                            visited[nb] = 1
                            comp.append(nb)
                            cq.append(nb)
        components.append((comp, (min_x, min_y, max_x, max_y)))

    if len(components) > 1:
        total_fg = sum(len(c[0]) for c in components)
        min_significant = max(6, int(total_fg * 0.0015))
        sig_boxes = [box for comp, box in components if len(comp) >= min_significant]
        if sig_boxes:
            gx0 = min(b[0] for b in sig_boxes) - 8
            gy0 = min(b[1] for b in sig_boxes) - 8
            gx1 = max(b[2] for b in sig_boxes) + 8
            gy1 = max(b[3] for b in sig_boxes) + 8
            for comp, (x0, y0, x1, y1) in components:
                if len(comp) < min_significant:
                    outside = x1 < gx0 or x0 > gx1 or y1 < gy0 or y0 > gy1
                    if outside or len(comp) <= 3:
                        for p in comp:
                            bg_mask[p] = 1

    # 7. Finalize binary alpha & zero RGB under transparent pixels
    transparent_count = 0
    for i in range(n_pixels):
        idx = i * 4
        if bg_mask[i]:
            buf[idx] = 0
            buf[idx + 1] = 0
            buf[idx + 2] = 0
            buf[idx + 3] = 0
            transparent_count += 1
        else:
            buf[idx + 3] = 255

    out = Image.frombytes("RGBA", (width, height), bytes(buf))
    return out, {
        "mode": mode,
        "key_color": f"#{kr:02X}{kg:02X}{kb:02X}",
        "transparent_pct": round(100.0 * transparent_count / max(1, n_pixels), 2),
    }


def compute_target_size(
    crop_w: int,
    crop_h: int,
    target_width: int | None,
    target_height: int | None,
) -> tuple[int, int]:
    if target_width is not None and target_height is not None:
        scale = min(target_width / crop_w, target_height / crop_h)
        return (max(1, round(crop_w * scale)), max(1, round(crop_h * scale)))
    if target_height is not None:
        scale = target_height / crop_h
        return (max(1, round(crop_w * scale)), max(1, target_height))
    if target_width is not None:
        scale = target_width / crop_w
        return (max(1, target_width), max(1, round(crop_h * scale)))
    return (crop_w, crop_h)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a chroma-key generated object into a transparent, room-scaled pixel-art sprite."
    )
    parser.add_argument("input_path", type=Path, help="Input image path (processed in-place unless --output is set).")
    parser.add_argument("--output", type=Path, default=None, help="Optional destination path if different from input_path.")
    parser.add_argument(
        "--delete-input",
        action="store_true",
        help="Delete input_path after writing --output so zero interim files remain.",
    )
    parser.add_argument(
        "--key-color",
        default="auto",
        help="Chroma key color: 'auto' (default), 'magenta', 'green', 'cyan', or '#RRGGBB'.",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=65,
        help="RGB Euclidean tolerance for chroma-key flood removal (default: 65).",
    )
    parser.add_argument("--target-height", type=int, default=None, help="Target sprite height in pixels.")
    parser.add_argument("--target-width", type=int, default=None, help="Target sprite width in pixels.")
    parser.add_argument(
        "--reference-bg",
        type=Path,
        default=None,
        help="Optional room background image used to compute proportional dimensions.",
    )
    parser.add_argument(
        "--height-ratio",
        type=float,
        default=None,
        help="Target sprite height as a fraction of --reference-bg height (or 590px default).",
    )
    parser.add_argument(
        "--width-ratio",
        type=float,
        default=None,
        help="Target sprite width as a fraction of --reference-bg width (or 1376px default).",
    )

    args = parser.parse_args()
    input_path: Path = args.input_path.resolve()
    output_path: Path = args.output.resolve() if args.output else input_path

    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    bg_w, bg_h = 1376, 590
    if args.reference_bg is not None:
        if not args.reference_bg.is_file():
            print(f"Error: reference background not found: {args.reference_bg}", file=sys.stderr)
            return 1
        with Image.open(args.reference_bg) as bg_im:
            bg_w, bg_h = bg_im.size

    target_height = args.target_height
    target_width = args.target_width
    if target_height is None and args.height_ratio is not None:
        target_height = max(1, round(bg_h * args.height_ratio))
    if target_width is None and args.width_ratio is not None:
        target_width = max(1, round(bg_w * args.width_ratio))

    with Image.open(input_path) as src_im:
        orig_size = src_im.size
        cleaned, meta = remove_background(
            src_im,
            key_spec=args.key_color,
            tolerance=args.tolerance,
        )

    bbox = cleaned.getbbox()
    if bbox is None:
        print("Error: entire image became transparent; check --key-color or --tolerance.", file=sys.stderr)
        return 1

    cropped = cleaned.crop(bbox)
    crop_w, crop_h = cropped.size
    out_w, out_h = compute_target_size(crop_w, crop_h, target_width, target_height)

    if (out_w, out_h) != (crop_w, crop_h):
        final_sprite = cropped.resize((out_w, out_h), resample=Image.Resampling.NEAREST)
    else:
        final_sprite = cropped

    # Encode to memory first so in-place writes never create interim temp files in the directory
    png_bytes = io.BytesIO()
    final_sprite.save(png_bytes, format="PNG", optimize=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(png_bytes.getvalue())

    if args.delete_input and input_path != output_path and input_path.exists():
        input_path.unlink()

    report = {
        "output": str(output_path),
        "original_size": list(orig_size),
        "cropped_size": [crop_w, crop_h],
        "final_size": [out_w, out_h],
        "reference_bg_size": [bg_w, bg_h],
        **meta,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
