#!/usr/bin/env python3
"""One single image holding all ten glass layouts, so they can be compared at once.

The chat viewer only ever shows one file, so every layout has to live inside a single
picture. Thumbs are 500x281 (16:9) on a 1520 px wide canvas - big enough to read the
layout, small enough that the JPEG stays well under the size that breaks the viewer.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "mockups" / "variants" / "liquid"
OUT = SRC / "00-liquid-choose.jpg"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size, bold=True):
    try:
        return ImageFont.truetype(str(FONT_DIR / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)
    except OSError:
        return ImageFont.load_default()


SHOTS = [
    "l01-floating-crystal", "l02-bottom-sheet", "l03-side-rail",
    "l04-split-glass", "l05-island-hop", "l06-tile-grid",
    "l07-settings-list", "l08-orbit", "l09-tab-bar", "l10-command-sheet",
]

TW, TH = 500, 281
GAP = 10
COLS = 3
HEAD = 38
W = COLS * TW + (COLS - 1) * GAP
ROWS = (len(SHOTS) + COLS - 1) // COLS
H = HEAD + ROWS * TH + (ROWS - 1) * GAP + 8


def main():
    canvas = Image.new("RGB", (W, H), (6, 14, 22))
    d = ImageDraw.Draw(canvas)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(6 + 10 * k), int(14 + 16 * k), int(22 + 18 * k)))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, -300, W * 0.6, 160], fill=(47, 233, 255, 34))
    gd.ellipse([W * 0.5, -280, W + 200, 140], fill=(217, 70, 239, 28))
    canvas = Image.alpha_composite(canvas.convert("RGBA"),
                                   glow.filter(ImageFilter.GaussianBlur(60))).convert("RGB")
    d = ImageDraw.Draw(canvas)

    for i, name in enumerate(SHOTS):
        col, row = i % COLS, i // COLS
        used = min(COLS, len(SHOTS) - row * COLS)
        row_w = used * TW + (used - 1) * GAP
        x0 = (W - row_w) // 2
        x = x0 + col * (TW + GAP)
        y = HEAD + row * (TH + GAP)

        thumb = Image.open(SRC / f"{name}.png").convert("RGB").resize((TW, TH), Image.LANCZOS)
        mask = Image.new("L", (TW, TH), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, TW - 1, TH - 1], 14, fill=255)
        canvas.paste(thumb, (x, y), mask)

        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([x, y, x + TW - 1, y + TH - 1], 14,
                            outline=(255, 255, 255, 150), width=1)

        label = str(i + 1)
        bw = 34 if len(label) == 1 else 44
        d.rounded_rectangle([x + 8, y + 8, x + 8 + bw, y + 34], 8, fill=(4, 16, 26, 225),
                            outline=(168, 245, 255, 210), width=1)
        d.text((x + 8 + bw / 2, y + 20), label, font=font(17), fill=(168, 245, 255), anchor="mm")

    canvas.save(OUT, "JPEG", quality=82, optimize=True, progressive=True)
    print(f"{OUT.relative_to(ROOT)}  {W}x{H}  {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
