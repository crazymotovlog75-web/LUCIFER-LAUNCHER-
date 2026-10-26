#!/usr/bin/env python3
"""Build a labelled contact sheet of the 10 launcher colour variants."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "mockups" / "variants"
OUT = VAR / "00-all-variants.png"

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

ROWS = [
    ("01", "v01-abyss-teal.png", "ABYSS TEAL", "current palette", (47, 233, 255), (217, 70, 239)),
    ("02", "v02-ember-forge.png", "EMBER FORGE", "molten orange", (255, 138, 46), (255, 196, 84)),
    ("03", "v03-frost-lich.png", "FROST LICH", "ice blue", (140, 220, 255), (186, 214, 255)),
    ("04", "v04-blood-moon.png", "BLOOD MOON", "crimson", (255, 86, 92), (255, 128, 156)),
    ("05", "v05-gilded-dusk.png", "GILDED DUSK", "champagne gold", (248, 208, 122), (196, 138, 66)),
    ("06", "v06-violet-void.png", "VIOLET VOID", "amethyst", (178, 140, 255), (232, 121, 249)),
    ("07", "v07-toxic-jade.png", "TOXIC JADE", "emerald + lime", (88, 230, 160), (163, 230, 53)),
    ("08", "v08-midnight-sapphire.png", "MIDNIGHT SAPPHIRE", "sapphire blue", (96, 165, 250), (129, 140, 248)),
    ("09", "v09-cyber-nocturne.png", "CYBER NOCTURNE", "neon cyan + hot pink", (38, 231, 255), (255, 62, 176)),
    ("10", "v10-bone-crypt.png", "BONE CRYPT", "bone + slate", (236, 224, 196), (160, 172, 184)),
]

CELL_W = 900            # thumbnail width
COLS = 2
PAD = 22
HEADER = 110
LABEL_H = 62
BG = (6, 7, 12)


def build(rows, out_path, title, subtitle):
    ROWS = rows
    OUT = out_path
    first = Image.open(VAR / ROWS[0][1]).convert("RGB")
    cell_h = round(CELL_W * first.height / first.width)

    rows = (len(ROWS) + COLS - 1) // COLS
    W = PAD + COLS * (CELL_W + PAD)
    H = HEADER + rows * (cell_h + LABEL_H + PAD) + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    f_title = ImageFont.truetype(FONT_B, 40)
    f_sub = ImageFont.truetype(FONT_B, 19)
    f_num = ImageFont.truetype(FONT_B, 26)
    f_name = ImageFont.truetype(FONT_B, 25)
    f_note = ImageFont.truetype(FONT_B, 17)

    d.text((PAD + 2, 24), title, font=f_title, fill=(245, 248, 255))
    d.text((PAD + 2, 66), subtitle, font=f_sub, fill=(150, 165, 180))

    for i, (num, fname, name, note, c1, c2) in enumerate(ROWS):
        col, row = i % COLS, i // COLS
        x = PAD + col * (CELL_W + PAD)
        y = HEADER + row * (cell_h + LABEL_H + PAD)

        shot = Image.open(VAR / fname).convert("RGB").resize((CELL_W, cell_h), Image.LANCZOS)
        sheet.paste(shot, (x, y))
        d.rectangle([x, y, x + CELL_W - 1, y + cell_h - 1], outline=(40, 46, 58), width=2)

        # label bar
        bar_y = y + cell_h
        d.rectangle([x, bar_y, x + CELL_W - 1, bar_y + LABEL_H - 6], fill=(12, 14, 20))
        d.rectangle([x, bar_y, x + CELL_W - 1, bar_y + LABEL_H - 6], outline=(40, 46, 58), width=2)

        # number chip
        d.rounded_rectangle([x + 10, bar_y + 8, x + 52, bar_y + 40], 6, fill=c1)
        nw = d.textlength(num, font=f_num)
        d.text((x + 31 - nw / 2, bar_y + 12), num, font=f_num, fill=(8, 10, 14))

        d.text((x + 66, bar_y + 8), name, font=f_name, fill=(245, 248, 255))
        d.text((x + 66, bar_y + 30), note, font=f_note, fill=(150, 165, 180))

        # swatches
        for j, c in enumerate((c1, c2)):
            sx = x + CELL_W - 34 - j * 26
            d.rounded_rectangle([sx, bar_y + 14, sx + 20, bar_y + 34], 5, fill=c, outline=(70, 76, 88))

    sheet.save(OUT, "PNG", optimize=True)
    print("wrote", OUT.relative_to(ROOT), sheet.size)


GLASS = [
    ("01", "glass/g01-frosted-abyss.png", "FROSTED ABYSS", "deep-sea glass · cyan edge", (150, 244, 255), (240, 168, 255)),
    ("02", "glass/g02-arctic-white.png", "ARCTIC WHITE", "silver-white glass", (236, 246, 255), (206, 224, 242)),
    ("03", "glass/g03-sapphire-glass.png", "SAPPHIRE GLASS", "blue pane · electric edge", (136, 196, 255), (176, 156, 255)),
    ("04", "glass/g04-rose-quartz.png", "ROSE QUARTZ", "pink glass · warm glow", (255, 198, 220), (255, 152, 196)),
    ("05", "glass/g05-emerald-glass.png", "EMERALD GLASS", "green pane · jade edge", (160, 255, 214), (198, 255, 152)),
    ("06", "glass/g06-amber-glass.png", "AMBER GLASS", "warm gold pane", (255, 218, 156), (255, 176, 118)),
    ("07", "glass/g07-violet-haze.png", "VIOLET HAZE", "amethyst glass · neon rim", (204, 176, 255), (255, 152, 238)),
    ("08", "glass/g08-liquid-chrome.png", "LIQUID CHROME", "smoked metal · mono", (238, 242, 248), (184, 196, 212)),
]


if __name__ == "__main__":
    build(ROWS, OUT,
          "LUCIFER LAUNCHER — 10 COLOUR VARIANTS",
          "same layout · same real skin · same BG10 wallpaper · only the palette changes")
    build(GLASS, VAR / "glass" / "00-glass-variants.png",
          "LUCIFER LAUNCHER — GLASS THEME (8 OPTIONS)",
          "frosted panes: blurred backdrop · tint wash · edge light · specular sheen")
