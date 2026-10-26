#!/usr/bin/env python3
"""Light JPEG copies + one 10-up contact sheet for the liquid-glass batch.

Everything is kept small (single screens 1280x720 / ~150 KB, sheet ~250 KB) so the
files open instantly in the chat viewer instead of timing out on a huge PNG.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "mockups" / "variants" / "liquid"
JPG = SRC / "jpg"

SHOTS = [
    ("l01", "l01-floating-crystal", "FLOATING CRYSTAL", "hero left · instances right"),
    ("l02", "l02-bottom-sheet", "BOTTOM SHEET", "wallpaper first · one sheet"),
    ("l03", "l03-side-rail", "SIDE RAIL", "vertical icon rail · wide hero"),
    ("l04", "l04-split-glass", "SPLIT GLASS", "two columns · recent worlds"),
    ("l05", "l05-island-hop", "ISLAND HOP", "floating islands · split dock"),
    ("l06", "l06-tile-grid", "TILE GRID", "header + six equal tiles"),
    ("l07", "l07-settings-list", "SETTINGS LIST", "iOS grouped rows + preview"),
    ("l08", "l08-orbit", "ORBIT", "circular core · orbiting nav"),
    ("l09", "l09-tab-bar", "TAB BAR", "wide hero · iOS tab bar"),
    ("l10", "l10-command-sheet", "COMMAND SHEET", "one squircle · 3 columns"),
]

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
REG = FONT_DIR / "DejaVuSans.ttf"


def font(size, bold=True):
    path = BOLD if bold else REG
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def light_copies():
    JPG.mkdir(parents=True, exist_ok=True)
    for key, name, _, _ in SHOTS:
        src = SRC / f"{name}.png"
        im = Image.open(src).convert("RGB").resize((1280, 720), Image.LANCZOS)
        out = JPG / f"{key}.jpg"
        im.save(out, "JPEG", quality=85, optimize=True, progressive=True)
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")


def sheet():
    W, H = 1600, 872
    top = Image.new("RGB", (W, H), (7, 18, 26))
    d = ImageDraw.Draw(top)
    for y in range(H):  # soft vertical wash
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(7 + 8 * k), int(18 + 12 * k), int(26 + 14 * k)))

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.05, -260, W * 0.62, 210], fill=(47, 233, 255, 40))
    gd.ellipse([W * 0.55, -240, W * 1.05, 190], fill=(217, 70, 239, 34))
    top = Image.alpha_composite(top.convert("RGBA"),
                                glow.filter(ImageFilter.GaussianBlur(70))).convert("RGB")
    d = ImageDraw.Draw(top)

    d.text((30, 24), "LUCIFER LAUNCHER", font=font(22), fill=(255, 255, 255))
    d.text((30 + 248, 33), "|   iPhone liquid crystal clear", font=font(15, False), fill=(168, 245, 255))
    d.text((30, 54), "10 layouts · 10 pictures · same real Abyss-Teal content",
           font=font(12, False), fill=(150, 176, 190))

    cell_w, cell_h = 372, 209
    gap_x, gap_y = 18, 14
    label_h = 32
    cols = 4
    grid_w = cols * cell_w + (cols - 1) * gap_x
    x0 = (W - grid_w) // 2
    y0 = 84

    for i, (key, name, title, sub) in enumerate(SHOTS):
        col, row = i % cols, i // cols
        x = x0 + col * (cell_w + gap_x)
        y = y0 + row * (cell_h + label_h + gap_y)
        thumb = Image.open(SRC / f"{name}.png").convert("RGB").resize((cell_w, cell_h), Image.LANCZOS)

        mask = Image.new("L", (cell_w, cell_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, cell_w - 1, cell_h - 1], 12, fill=255)
        top.paste(thumb, (x, y), mask)
        d = ImageDraw.Draw(top)
        d.rounded_rectangle([x, y, x + cell_w - 1, y + cell_h - 1], 12,
                            outline=(255, 255, 255, 120), width=1)
        d.text((x + 2, y + cell_h + 5), key.upper(), font=font(13), fill=(168, 245, 255))
        d.text((x + 32, y + cell_h + 6), title, font=font(11), fill=(255, 255, 255))
        d.text((x + 2, y + cell_h + 23), sub, font=font(9, False), fill=(140, 168, 182))

    out = SRC / "00-liquid-10up.jpg"
    top.save(out, "JPEG", quality=86, optimize=True, progressive=True)
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    light_copies()
    sheet()
