#!/usr/bin/env python3
"""Renders the bundled "Liquid Crystal" wallpaper (aurora) that the glass panes refract.

Uses the exact backdrop routine of the approved L03 mockup so the shipped launcher looks like
the picture the layout was picked from. Output is written straight into the UI overlay:

    launcher-ui-overhaul/.../drawable-nodpi/lucifer_wallpaper_22.webp
    launcher-ui-overhaul/.../drawable-nodpi/lucifer_wallpaper_preview_22.webp
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_liquid_glass as glass  # noqa: E402

OUT_DIR = (ROOT / "launcher-ui-overhaul" / "app_pojavlauncher" / "src" / "main"
           / "res" / "drawable-nodpi")

FULL = (1600, 900)
PREVIEW = (600, 338)


def render(size):
    width, height = size
    glass.W = width
    glass.H = height
    glass.S = 1
    art = glass.build_bg()

    # A gentle vertical lift keeps white glass type readable on the lower half, exactly like the
    # mockup, without turning the wallpaper into a dark scene.
    veil = Image.new("RGBA", art.size, (0, 0, 0, 0))
    pixels = veil.load()
    for y in range(height):
        t = y / (height - 1)
        alpha = int(18 + 30 * (t ** 1.6))
        for x in range(0, width, 8):
            for dx in range(8):
                if x + dx < width:
                    pixels[x + dx, y] = (12, 26, 40, alpha)
    return Image.alpha_composite(art.convert("RGBA"), veil).convert("RGB")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    full = render(FULL)
    out = OUT_DIR / "lucifer_wallpaper_22.webp"
    full.save(out, "WEBP", quality=88, method=6)
    print(f"{out.relative_to(ROOT)}  {full.size[0]}x{full.size[1]}  {out.stat().st_size // 1024} KB")

    preview = full.resize(PREVIEW, Image.LANCZOS).filter(ImageFilter.SMOOTH)
    pout = OUT_DIR / "lucifer_wallpaper_preview_22.webp"
    preview.save(pout, "WEBP", quality=84, method=6)
    print(f"{pout.relative_to(ROOT)}  {preview.size[0]}x{preview.size[1]}  {pout.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
