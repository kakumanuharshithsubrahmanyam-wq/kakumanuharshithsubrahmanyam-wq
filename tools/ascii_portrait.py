#!/usr/bin/env python3
"""Turn a segmented portrait cutout into an animated ASCII-art SVG.

Input is the RGBA cutout produced by tools/Segment.swift (background already
transparent) plus its JSON sidecar containing the Vision face rectangle.

The alpha channel decides the silhouette and the luminance decides which
density character is used, so every pixel inside the subject gets a visible
glyph and the outline never dissolves into the white shirt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter

# Light to dark, with index 0 reserved for "outside the subject".
#
# These glyphs were chosen by measuring each candidate's actual ink coverage in
# Menlo at a 0.6em cell and picking evenly spaced steps, so a linear darkness
# value maps to a linear change in apparent tone. Hand-picked ramps are usually
# non-monotonic -- "%" covers less ink than "#" or even "S" despite looking
# heavier in a text editor, which inverts tones around the midpoint.
# Rerun with --calibrate to re-derive this.
RAMP = " `.-:;=cfFwPU#0@"

CALIBRATION_POOL = " `.-:;+=ilcvxtsfJCunFIoewhkZaSXPEGmpqAbdUO#8Q0WBM@"

# Monospace advance width as a fraction of font size. Menlo, SF Mono, Consolas
# and DejaVu Sans Mono all use 0.6em, and textLength pins the row width anyway.
CHAR_ASPECT = 0.6


def calibrate(font_path: str, levels: int) -> str:
    """Derive a ramp whose glyphs step evenly through measured ink coverage."""
    from PIL import ImageDraw, ImageFont

    size = 64
    font = ImageFont.truetype(font_path, size)
    cell = (int(round(size * CHAR_ASPECT)), size)
    cov = {}
    for ch in CALIBRATION_POOL:
        im = Image.new("L", cell, 255)
        ImageDraw.Draw(im).text((0, size * 0.80), ch, font=font, fill=0, anchor="ls")
        cov[ch] = 1.0 - np.asarray(im, dtype=np.float32).mean() / 255.0

    top = max(cov.values())
    ramp = []
    for k in range(levels):
        target = top * k / (levels - 1)
        ch = min(cov, key=lambda c: abs(cov[c] - target))
        if ch not in ramp:
            ramp.append(ch)
    return "".join(ramp)


def load_face_box(meta_path: Path, width: int, height: int):
    """Return the face rectangle in top-left-origin pixels."""
    meta = json.loads(meta_path.read_text())
    face = meta.get("face")
    if not face:
        raise SystemExit("no face rectangle in sidecar; cannot frame the crop")
    fw = face["w"] * width
    fh = face["h"] * height
    fx = face["x"] * width
    # Vision reports a bottom-left origin.
    fy = (1.0 - face["y"] - face["h"]) * height
    return fx, fy, fw, fh


def crop_box(img: Image.Image, face, top_pad: float, bottom_pad: float, width_mult: float):
    """Frame the head only, measured in multiples of the face box.

    Cropping at the neck is what keeps the portrait readable: including the
    shoulders drags in the near-white polo shirt, which has almost no tonal
    range and renders as a wide smear of faint characters.
    """
    fx, fy, fw, fh = face
    cx = fx + fw / 2.0

    top = fy - fh * top_pad
    bottom = fy + fh + fh * bottom_pad
    crop_w = fw * width_mult
    left = cx - crop_w / 2.0

    left = max(0.0, left)
    top = max(0.0, top)
    right = min(float(img.width), left + crop_w)
    bottom = min(float(img.height), bottom)
    return (round(left), round(top), round(right), round(bottom))


def to_rows(img: Image.Image, rows: int, alpha_cut: int, low_pct: float,
            high_pct: float, gamma: float, sharpen: int, local: float,
            mix: float, ramp: str, face_cells=None, face_tone: float = 0.0,
            edge: float = 0.0, face_contrast: float = 1.0,
            body_lift: float = 0.0, body_cap: float = 0.42):
    """Downsample to a character grid and map each cell to a ramp character."""
    aspect = img.width / img.height
    cols = max(1, round(aspect * rows / CHAR_ASPECT))

    # Composite over white before desaturating. Converting RGBA straight to "L"
    # makes transparent pixels black, which both skews the tonal statistics and
    # paints a false dark halo around the silhouette.
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.alpha_composite(img)
    grey = white.convert("L")
    if sharpen > 0:
        grey = grey.filter(ImageFilter.UnsharpMask(radius=sharpen, percent=120, threshold=3))

    low = grey.resize((cols, rows), Image.LANCZOS)
    mask = np.asarray(img.split()[-1].resize((cols, rows), Image.LANCZOS)) >= alpha_cut

    small = np.asarray(low, dtype=np.float32)
    if local > 0:
        # Boost local contrast *at grid scale*, not at full resolution. The
        # glasses, eyes and mouth are only a couple of cells wide here, so any
        # sharpening done before the downsample is simply averaged away.
        base = np.asarray(low.filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float32)
        small = np.clip(small + local * (small - base), 0.0, 255.0)

    if not mask.any():
        raise SystemExit("alpha cut removed the whole subject")

    lo, hi = np.percentile(small[mask], [low_pct, high_pct])
    if hi - lo < 1e-3:
        hi = lo + 1.0
    stretched = np.clip((small - lo) / (hi - lo), 0.0, 1.0)

    if mix > 0:
        # Rank-map the subject's tones so every ramp level gets used, then blend
        # back toward the linear stretch. Pure equalisation opens up the face but
        # erases the dark mass of the hair, which is what makes the head read as
        # a head; pure stretching does the opposite.
        ref = np.sort(small[mask])
        equalised = np.interp(small, ref, np.linspace(0.0, 1.0, ref.size))
        norm = (1.0 - mix) * stretched + mix * equalised
    else:
        norm = stretched

    # Clamp before the power: rounding in the blend can leave norm a hair above
    # 1.0, and a negative base with a fractional exponent yields NaN.
    linear = np.clip(1.0 - np.clip(norm, 0.0, 1.0), 0.0, 1.0)

    if face_cells is not None and face_tone > 0:
        # Expose for the face rather than for the whole silhouette. Normalising
        # across everything drags mid-tone skin into the dense half of the ramp,
        # where every glyph reads as solid dark and the features stop resolving.
        fy0, fy1, fx0, fx1 = face_cells
        region = linear[fy0:fy1, fx0:fx1][mask[fy0:fy1, fx0:fx1]]
        if region.size:
            med = float(np.median(region))
            med = min(max(med, 0.02), 0.98)
            gamma = np.log(face_tone) / np.log(med)

    darkness = linear ** gamma

    if face_contrast != 1.0 and face_tone > 0:
        # Expand tonal range about the face's own level. Simply aiming for a
        # darker face median adds ink without definition and swallows the
        # glasses; pivoting here holds the face's brightness while pushing the
        # shadows down and the highlights up, so features separate.
        darkness = np.clip(face_tone + (darkness - face_tone) * face_contrast, 0.0, 1.0)

    if edge > 0:
        # Trace the silhouette. A bust crop includes the near-white polo shirt,
        # which carries so little tonal range that the shoulders would otherwise
        # dissolve into blanks; drawing the contour keeps the shape legible
        # without filling the garment in with a flat grey wash.
        m = mask.astype(np.float32)
        inner = np.ones_like(m)
        for shift, axis in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
            inner = np.minimum(inner, np.roll(m, shift, axis=axis))
        boundary = np.clip(m - inner, 0.0, 1.0)
        soft = np.asarray(
            Image.fromarray((boundary * 255).astype(np.uint8), mode="L")
            .filter(ImageFilter.GaussianBlur(0.7)),
            dtype=np.float32,
        ) / 255.0
        darkness = np.maximum(darkness, np.clip(soft, 0.0, 1.0) * edge)

    if body_lift > 0 and face_cells is not None:
        # Softly recover shirt / shoulder / arm structure below the face without
        # crushing highlights into a flat grey wash. Attract faint body cells
        # toward a light midtone, then hard-cap so the polo never goes dark.
        fy1 = face_cells[1]
        body = darkness[fy1:, :]
        target = np.minimum(body_cap, body + body_lift * (body_cap - body))
        lifted = np.where(mask[fy1:, :], np.maximum(body, target), body)
        darkness[fy1:, :] = np.clip(lifted, 0.0, body_cap)

    top = len(ramp) - 1
    # The brightest parts of the face are allowed to fall through to a blank.
    # Forcing a glyph onto every pixel inside the silhouette is what turns the
    # portrait into a solid mass; the highlights need to breathe.
    idx = np.clip(np.rint(darkness * top).astype(int), 0, top)
    idx = np.where(mask, idx, 0)

    lut = np.array(list(ramp))
    return ["".join(lut[row]).rstrip() for row in idx], cols


def build_svg(rows_text, cols, font_size, line_height, pad, stagger, duration,
              grad_from, grad_mid, grad_to, label):
    char_w = font_size * CHAR_ASPECT
    text_w = cols * char_w
    width = round(text_w + pad * 2)
    height = round(len(rows_text) * line_height + pad * 2)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">',
        f"<title>{escape(label)}</title>",
        "<style>",
        "@keyframes apf{from{opacity:0}to{opacity:1}}",
        f".l{{opacity:0;animation:apf {duration}s ease-out both}}",
        "@media (prefers-reduced-motion: reduce){"
        ".l{animation:none!important;opacity:1!important}}",
        "</style>",
        "<defs>",
        f'<linearGradient id="apg" gradientUnits="userSpaceOnUse" '
        f'x1="{pad}" y1="{pad}" x2="{pad + text_w}" y2="{height - pad}">',
        f'<stop offset="0" stop-color="{grad_from}"/>',
        f'<stop offset=".55" stop-color="{grad_mid}"/>',
        f'<stop offset="1" stop-color="{grad_to}"/>',
        "</linearGradient>",
        "</defs>",
        f'<g fill="url(#apg)" font-size="{font_size:g}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    ]

    baseline = pad + font_size * 0.82
    for i, line in enumerate(rows_text):
        if not line.strip():
            continue
        y = baseline + i * line_height
        # xml:space has to sit on each text element; browsers do not inherit it
        # from the group for layout, and without it the leading spaces that
        # position each row collapse and flatten the silhouette flush left.
        # textLength must likewise match this row's own character count, or
        # sparse rows get stretched edge to edge.
        parts.append(
            f'<text class="l" style="animation-delay:{i * stagger:.3f}s" '
            f'xml:space="preserve" x="{pad}" y="{y:.2f}" '
            f'textLength="{len(line) * char_w:.2f}" '
            f'lengthAdjust="spacing">{escape(line)}</text>'
        )

    parts.append("</g></svg>")
    return "\n".join(parts), width, height


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cutout", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--meta", type=Path, default=None)
    p.add_argument("--rows", type=int, default=185)
    p.add_argument("--top-pad", type=float, default=0.52,
                   help="hair room above the face box, in face heights")
    p.add_argument("--bottom-pad", type=float, default=1.9,
                   help="room below the face box, in face heights; ~1.9 reaches the arms")
    p.add_argument("--width-mult", type=float, default=3.1,
                   help="crop width in multiples of the face width")
    p.add_argument("--alpha-cut", type=int, default=110)
    p.add_argument("--low-pct", type=float, default=2.0)
    p.add_argument("--high-pct", type=float, default=98.0)
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--sharpen", type=int, default=6)
    p.add_argument("--local", type=float, default=1.0,
                   help="local contrast boost; 0 disables")
    p.add_argument("--mix", type=float, default=0.2,
                   help="blend toward rank equalisation, 0..1")
    p.add_argument("--calibrate", action="store_true",
                   help="re-derive the density ramp from measured ink coverage")
    p.add_argument("--calibrate-font", default="/System/Library/Fonts/Menlo.ttc")
    p.add_argument("--levels", type=int, default=16)
    p.add_argument("--face-contrast", type=float, default=1.0,
                   help="tonal range expansion pivoted on --face-tone; 1 disables")
    p.add_argument("--edge", type=float, default=0.45,
                   help="silhouette contour strength, 0..1; 0 disables")
    p.add_argument("--body-lift", type=float, default=0.0,
                   help="recover shirt/shoulder/arm midtones below the face, 0..1")
    p.add_argument("--body-cap", type=float, default=0.42,
                   help="hard ceiling for body darkness so the shirt stays light")
    p.add_argument("--face-tone", type=float, default=0.56,
                   help="target median darkness of the face, 0..1; 0 uses --gamma")
    p.add_argument("--font-size", type=float, default=7.2)
    p.add_argument("--line-height", type=float, default=7.2)
    p.add_argument("--pad", type=float, default=10)
    p.add_argument("--stagger", type=float, default=0.018)
    p.add_argument("--duration", type=float, default=0.35)
    p.add_argument("--from-color", default="#1d4ed8")
    p.add_argument("--mid-color", default="#4f46e5")
    p.add_argument("--to-color", default="#7c3aed")
    p.add_argument("--label", default="ASCII-art portrait")
    p.add_argument("--txt", type=Path, default=None, help="also write a plain-text preview")
    args = p.parse_args()

    ramp = RAMP
    if args.calibrate:
        ramp = calibrate(args.calibrate_font, args.levels)
        print(f"calibrated ramp: {ramp!r}")

    img = Image.open(args.cutout).convert("RGBA")
    meta = args.meta or Path(str(args.cutout) + ".json")
    face = load_face_box(meta, img.width, img.height)

    box = crop_box(img, face, args.top_pad, args.bottom_pad, args.width_mult)
    fx, fy, fw, fh = face
    img = img.crop(box)

    # Face rectangle expressed in character cells of the final grid.
    aspect = img.width / img.height
    cols_est = max(1, round(aspect * args.rows / CHAR_ASPECT))
    cells = (
        int(max(0, (fy - box[1]) / img.height * args.rows)),
        int(min(args.rows, (fy + fh - box[1]) / img.height * args.rows)),
        int(max(0, (fx - box[0]) / img.width * cols_est)),
        int(min(cols_est, (fx + fw - box[0]) / img.width * cols_est)),
    )

    rows_text, cols = to_rows(img, args.rows, args.alpha_cut, args.low_pct,
                              args.high_pct, args.gamma, args.sharpen, args.local,
                              args.mix, ramp, cells, args.face_tone, args.edge,
                              args.face_contrast, args.body_lift, args.body_cap)
    svg, w, h = build_svg(rows_text, cols, args.font_size, args.line_height, args.pad,
                          args.stagger, args.duration, args.from_color, args.mid_color,
                          args.to_color, args.label)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg)
    if args.txt:
        args.txt.write_text("\n".join(rows_text))

    filled = sum(len(r.strip()) for r in rows_text)
    print(f"crop={box} face_cells={cells} grid={cols}x{len(rows_text)} glyphs={filled} "
          f"svg={w}x{h} bytes={len(svg)}")


if __name__ == "__main__":
    main()
