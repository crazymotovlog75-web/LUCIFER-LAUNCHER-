#!/usr/bin/env python3
"""Frosted-glass colourways of the LUCIFER LAUNCHER home screen.

Same reconstruction as render_launcher_screens.py (real layouts, real drawables, real skin
atlas, shipped BG10 wallpaper) — the panels are swapped for glassmorphism panes:
blurred backdrop, tint wash, edge light and a specular sheen.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import render_launcher_screens as base

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mockups" / "variants" / "glass"


def darker(c, t):
    return tuple(int(round(v * (1 - t))) for v in c)


_BASE_BG = base.build_bg


def glass_bg(p):
    """A more luminous, more colourful backdrop so the frosted panes have something to smear."""
    art = _BASE_BG(p)
    # glass needs something luminous behind it: undo the dark wash and push the colour
    art = ImageEnhance.Brightness(art).enhance(1.85)
    art = ImageEnhance.Color(art).enhance(1.90)
    art = ImageEnhance.Contrast(art).enhance(1.06)

    glow = Image.new("RGBA", art.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    w, h = art.size
    g = p["glass"]
    orbs = g.get("orbs", [])
    for (cx, cy, r, color, a) in orbs:
        gd.ellipse([cx * w - r * w, cy * h - r * h, cx * w + r * w, cy * h + r * h],
                   fill=base.rgba(color, a))
    glow = glow.filter(ImageFilter.GaussianBlur(w // 14))
    return Image.alpha_composite(art.convert("RGBA"), glow).convert("RGB")


base.build_bg = glass_bg  # render() resolves this at call time

WHITE = (255, 255, 255)


def palette(slug, name, note, cyan, magenta, tint_top, tint_bottom, alpha=104, orbs=None,
            edge=WHITE, edge_alpha=180, blur=10, panel=None, panel_hi=None):
    panel = panel or darker(tint_bottom, 0.55)
    panel_hi = panel_hi or darker(tint_top, 0.35)
    return dict(
        slug=slug, name=name, note=note,
        cyan=cyan, magenta=magenta,
        panel=panel, panel_hi=panel_hi,
        wall_mix=0.30,
        glass=dict(blur=blur, brighten=1.24, saturate=1.05, contrast=1.02,
                   tint_top=tint_top, tint_bottom=tint_bottom, tint_alpha=alpha,
                   sheen=26, edge=edge, edge_alpha=edge_alpha, shadow=1.0, leak=1.0,
                   top_line=190, grain=12, orbs=orbs or []),
    )


PALETTES = [
    palette("g01-frosted-abyss", "FROSTED ABYSS", "deep-sea glass · cyan edge light",
            cyan=(150, 244, 255), magenta=(240, 168, 255),
            tint_top=(196, 236, 246), tint_bottom=(120, 176, 196), alpha=60,
            orbs=[(0.22, 0.18, 0.26, (0, 210, 255), 70),
                  (0.78, 0.22, 0.24, (217, 70, 239), 60),
                  (0.52, 0.86, 0.30, (0, 160, 200), 45)]),
    palette("g02-arctic-white", "ARCTIC WHITE", "silver-white glass · cool and clean",
            cyan=(236, 246, 255), magenta=(206, 224, 242),
            tint_top=(236, 244, 252), tint_bottom=(150, 170, 190), alpha=58,
            orbs=[(0.20, 0.20, 0.28, (200, 230, 255), 80),
                  (0.80, 0.26, 0.26, (170, 200, 230), 62),
                  (0.50, 0.88, 0.30, (140, 180, 220), 40)]),
    palette("g03-sapphire-glass", "SAPPHIRE GLASS", "blue pane · electric edge",
            cyan=(136, 196, 255), magenta=(176, 156, 255),
            tint_top=(176, 210, 252), tint_bottom=(104, 138, 196), alpha=62,
            orbs=[(0.24, 0.16, 0.26, (56, 132, 255), 85),
                  (0.80, 0.30, 0.24, (140, 90, 255), 60),
                  (0.50, 0.88, 0.30, (40, 90, 200), 45)]),
    palette("g04-rose-quartz", "ROSE QUARTZ", "pink glass · soft warm glow",
            cyan=(255, 198, 220), magenta=(255, 152, 196),
            tint_top=(252, 206, 222), tint_bottom=(196, 138, 168), alpha=62,
            orbs=[(0.22, 0.20, 0.26, (255, 110, 170), 80),
                  (0.80, 0.24, 0.26, (255, 170, 120), 55),
                  (0.50, 0.88, 0.30, (200, 60, 140), 45)]),
    palette("g05-emerald-glass", "EMERALD GLASS", "green pane · jade edge light",
            cyan=(160, 255, 214), magenta=(198, 255, 152),
            tint_top=(10, 38, 28), tint_bottom=(4, 18, 14), alpha=142,
            orbs=[(0.22, 0.18, 0.26, (30, 220, 150), 80),
                  (0.80, 0.26, 0.24, (150, 230, 60), 55),
                  (0.50, 0.88, 0.30, (10, 140, 110), 45)]),
    palette("g06-amber-glass", "AMBER GLASS", "warm gold pane · sunset light",
            cyan=(255, 218, 156), magenta=(255, 176, 118),
            tint_top=(252, 226, 186), tint_bottom=(202, 164, 118), alpha=62,
            orbs=[(0.22, 0.18, 0.26, (255, 170, 60), 80),
                  (0.80, 0.26, 0.24, (255, 110, 60), 55),
                  (0.50, 0.88, 0.30, (180, 90, 30), 45)]),
    palette("g07-violet-haze", "VIOLET HAZE", "amethyst glass · neon rim",
            cyan=(204, 176, 255), magenta=(255, 152, 238),
            tint_top=(214, 196, 252), tint_bottom=(150, 128, 204), alpha=64,
            orbs=[(0.22, 0.18, 0.26, (150, 90, 255), 85),
                  (0.80, 0.26, 0.24, (255, 90, 220), 60),
                  (0.50, 0.88, 0.30, (90, 60, 200), 45)]),
    palette("g08-liquid-chrome", "LIQUID CHROME", "smoked metal glass · mono",
            cyan=(238, 242, 248), magenta=(184, 196, 212),
            tint_top=(232, 238, 244), tint_bottom=(148, 158, 172), alpha=66,
            orbs=[(0.22, 0.18, 0.26, (200, 210, 225), 70),
                  (0.80, 0.26, 0.24, (150, 160, 180), 52),
                  (0.50, 0.88, 0.30, (110, 120, 140), 40)],
            edge=(255, 255, 255), edge_alpha=200, blur=12),
    palette("g09-crimson-glass", "CRIMSON GLASS", "blood-red pane · dark edge",
            cyan=(255, 176, 178), magenta=(255, 122, 158),
            tint_top=(252, 196, 200), tint_bottom=(180, 108, 124), alpha=64,
            orbs=[(0.22, 0.18, 0.26, (255, 60, 90), 90),
                  (0.80, 0.26, 0.24, (200, 30, 80), 70),
                  (0.50, 0.88, 0.30, (140, 20, 60), 55)],
            edge=(255, 232, 232), edge_alpha=190, blur=10),
    palette("g10-aurora-glass", "AURORA GLASS", "multi-colour aurora · iridescent",
            cyan=(178, 255, 244), magenta=(214, 176, 255),
            tint_top=(206, 250, 244), tint_bottom=(150, 168, 232), alpha=60,
            orbs=[(0.20, 0.16, 0.28, (0, 240, 200), 90),
                  (0.50, 0.30, 0.24, (120, 90, 255), 75),
                  (0.82, 0.22, 0.26, (255, 90, 200), 70),
                  (0.50, 0.90, 0.32, (0, 170, 220), 50)],
            edge=(240, 255, 252), edge_alpha=200, blur=11),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) or None
    for p in PALETTES:
        if only and p["slug"] not in only:
            continue
        print("wrote", base.render(p, out_dir=OUT).relative_to(ROOT))


if __name__ == "__main__":
    main()
