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

CELL_W = 760            # thumbnail width
COLS = 2
PAD = 22
HEADER = 96
LABEL_H = 54
BG = (6, 7, 12)


def main():
    first = Image.open(VAR / ROWS[0][1]).convert("RGB")
    cell_h = round(CELL_W * first.height / first.width)

    rows = (len(ROWS) + COLS - 1) // COLS
    W = PAD + COLS * (CELL_W + PAD)
    H = HEADER + rows * (cell_h + LABEL_H + PAD) + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    f_title = ImageFont.truetype(FONT_B, 34)
    f_sub = ImageFont.truetype(FONT_B, 16)
    f_num = ImageFont.truetype(FONT_B, 22)
    f_name = ImageFont.truetype(FONT_B, 21)
    f_note = ImageFont.truetype(FONT_B, 14)

    d.text((PAD + 2, 24), "LUCIFER LAUNCHER — 10 COLOUR VARIANTS", font=f_title, fill=(245, 248, 255))
    d.text((PAD + 2, 66), "same layout · same real skin · same BG10 wallpaper · only the palette changes",
           font=f_sub, fill=(150, 165, 180))

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


if __name__ == "__main__":
    main()
