#!/usr/bin/env python3
"""Three refinements of the launcher UI that is live right now.

No glass, no new theme: the same Abyss-Teal crystal cards, cyan/magenta HUD language and the
same dock that ships in the app. What changes is the composition and the type rhythm.

  A  HUD CLEAN    three tidy columns, everything on the same baseline grid
  B  CONSOLE      telemetry strip, one big hero, right-hand stack, footer row
  C  CARD DECK    hero plus a horizontal instance deck with big thumbnails

Run: python3 scripts/render_refined_hud.py [a b c]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

import render_launcher_screens as base

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mockups" / "variants" / "refined"

W, H = base.W, base.H
S = base.S
PAD = 20

PALETTE = dict(base.PALETTES[0])          # v01 ABYSS TEAL, the palette that ships
CYAN = PALETTE["cyan"]
MAGENTA = PALETTE["magenta"]
WHITE = (255, 255, 255)
TEXT = (255, 255, 255)
TEXT_2 = (196, 212, 222)
TEXT_3 = (138, 160, 172)
OK = (52, 211, 153)

MODS = ["Sodium", "Iris", "Lithium", "Krypton", "Ferrite"]
DOCK_TOP = H - 16 - 58


# --------------------------------------------------------------------------- atoms
def label(sc, x, y, s, col=TEXT_3, size=7.4, track=1.5):
    sc.text(x, y, s, size, col, True, track)


def value(sc, x, y, s, col=TEXT, size=13, track=0.0):
    sc.text(x, y, s, size, col, True, track)


def chip(sc, x, y, s, size=7.6, accent=None, pad=9, h=19, filled=False):
    """Small HUD pill. filled=True uses the accent as the plate (for the one call-to-action)."""
    tw = sc.width_of(s, size, True, 0.7)
    w = tw + pad * 2
    if filled:
        sc.grad_rect(x, y, w, h, base.lerp(accent or CYAN, WHITE, 0.45), accent or CYAN, radius=h / 2)
        sc.text_mid(x + w / 2, y + (h - size * 1.02) / 2, s, size, (8, 16, 22), True, 0.7)
    else:
        sc.rect(x, y, w, h, base.rgba(PALETTE["panel"], 190), radius=h / 2,
                outline=base.rgba(CYAN, 120), width=1)
        sc.text_mid(x + w / 2, y + (h - size * 1.02) / 2, s, size, TEXT_2, True, 0.7)
    return w


def dot(sc, cx, cy, r, col=OK):
    sc.ellipse(cx - r, cy - r, r * 2, r * 2, fill=base.rgba(col, 255))
    sc.halo(cx, cy, r * 3.4, col, 80)


def hero_skin(sc, cx, feet_y, height):
    """Full-body front sprite, feet on feet_y, with the stage glow the app uses."""
    sprite = base.skin_sprite(scale=14)
    h = int(height)
    w = h * sprite.width / sprite.height
    sc.halo(cx, feet_y - h * 0.52, w * 0.72, CYAN, 46)
    img = sprite.resize((int(w * S), int(h * S)), Image.LANCZOS)
    sc.img.alpha_composite(img, (sc.s(cx - w / 2), sc.s(feet_y - h)))
    sc.redraw()
    # plinth
    sc.ellipse(cx - w * 0.62, feet_y - 4, w * 1.24, 12, fill=base.rgba(CYAN, 26),
               outline=base.rgba(CYAN, 90), width=1)
    return w, h


def panel(sc, x, y, w, h, glow=False, radius=12):
    sc.card(x, y, w, h, PALETTE, radius=radius, glow=glow)


def panel_title(sc, x, y, w, text, right=None, right_col=CYAN):
    label(sc, x + 14, y + 12, text)
    if right:
        sc.text_end(x + w - 14, y + 12, right, 7.4, right_col, True, 0.8)


def instance_row(sc, x, y, w, h, title, sub, version, active=False):
    if active:
        sc.rect(x, y, w, h, base.rgba(CYAN, 20), radius=9, outline=base.rgba(CYAN, 190), width=1.3)
    else:
        sc.rect(x, y, w, h, base.rgba(PALETTE["panel_hi"], 150), radius=9,
                outline=base.rgba(WHITE, 26), width=1)
    # block thumb
    t = h - 16
    sc.rect(x + 8, y + 8, t, t, base.rgba(base.lerp(CYAN, PALETTE["panel"], 0.55), 220), radius=7,
            outline=base.rgba(CYAN, 150), width=1)
    k = t * 0.28
    sc.poly([(x + 8 + t / 2, y + 8 + t / 2 - k * 0.8), (x + 8 + t / 2 + k, y + 8 + t / 2 - k * 0.2),
             (x + 8 + t / 2, y + 8 + t / 2 + k * 0.44), (x + 8 + t / 2 - k, y + 8 + t / 2 - k * 0.2)],
            fill=base.rgba(WHITE, 200))
    tx = x + 8 + t + 12
    value(sc, tx, y + 10, title, TEXT, 10.5, 0.2)
    label(sc, tx, y + 27, sub, TEXT_3, 7.2, 1.0)
    sc.text_end(x + w - 12, y + 11, version, 7.2, TEXT_2, True, 0.6)
    if active:
        dot(sc, x + w - 22, y + h - 16, 3.0, CYAN)


def mods_plate(sc, x, y, w, h=40):
    panel(sc, x, y, w, h, radius=h / 2)
    label(sc, x + 16, y + h / 2 - 5, "TOP MODS")
    cx = x + 94
    for m in MODS:
        cw = chip(sc, cx, y + h / 2 - 9.5, m, size=7.4, h=19, pad=8)
        cx += cw + 8


def launch_button(sc, x, y, w, h=38, text="READY TO LAUNCH", size=9):
    sc.grad_rect(x, y, w, h, base.lerp(CYAN, WHITE, 0.50), CYAN, radius=h / 2)
    sc.glow_rect = None
    # play triangle
    cx, cy = x + 22, y + h / 2
    sc.poly([(cx - 4, cy - 6), (cx + 7, cy), (cx - 4, cy + 6)], fill=base.rgba((8, 16, 22), 255))
    sc.text(x + 40, y + (h - size * 1.15) / 2, text, size, (8, 16, 22), True, 0.9)


# --------------------------------------------------------------------------- A · HUD CLEAN
def variant_a(sc):
    base.header(sc, PALETTE)
    top, bottom = 84, 752

    # ---- column 1: instances / server / mods
    x1, w1 = PAD, 400
    panel(sc, x1, top, w1, 336, glow=True)
    panel_title(sc, x1, top, w1, "MY INSTANCES", "4 / 12")
    for i, (t, sub, ver, act) in enumerate((("Fabric 1.21.10", "SHADOW PVP · READY", "1.21.10", True),
                                            ("LuciferMC SMP", "LIFESTEEL · ONLINE", "1.21.4", False),
                                            ("CS Client", "PVP · 1.8.9", "1.8.9", False))):
        instance_row(sc, x1 + 12, top + 40 + i * 92, w1 - 24, 82, t, sub, ver, active=act)
    sc.rect(x1 + 12, top + 318, w1 - 24, 1, base.rgba(WHITE, 24), radius=1)
    sc.text(x1 + 14, top + 306, "", 8, TEXT_3)

    panel(sc, x1, 436, w1, 150)
    panel_title(sc, x1, 436, w1, "SERVER")
    value(sc, x1 + 14, 456, "LUCIFERMC", TEXT, 13, 0.6)
    label(sc, x1 + 14, 475, "LIFESTEEL SMP · play.lucifermc.fun", CYAN, 7.6, 0.4)
    dot(sc, x1 + 22, 500, 3.0)
    sc.text(x1 + 32, 494, "LIVE · 24ms · 12/200 players", 8.4, OK, True, 0.4)
    sc.rect(x1 + 14, 516, w1 - 28, 5, base.rgba(WHITE, 30), radius=3)
    sc.grad_rect(x1 + 14, 516, (w1 - 28) * 0.06, 5, base.lerp(CYAN, WHITE, 0.4), CYAN, radius=3)
    sc.text_end(x1 + w1 - 14, 486, "24ms", 9, OK, True, 0.4)

    panel(sc, x1, 602, w1, 150)
    panel_title(sc, x1, 602, w1, "MODS", "42 ACTIVE", OK)
    for i, m in enumerate(MODS[:4]):
        yy = 626 + i * 26
        dot(sc, x1 + 20, yy + 5, 2.4, CYAN)
        sc.text(x1 + 30, yy - 1, m, 9.2, TEXT, True, 0.4)
        sc.text_end(x1 + w1 - 14, yy - 1, "v2.%d" % (i + 3), 7.4, TEXT_3, True, 0.4)

    # ---- column 2: hero + recent worlds
    x2, w2 = 436, 700
    panel(sc, x2, top, w2, 480, glow=True, radius=14)
    label(sc, x2 + 20, top + 16, "FABRIC 1.21.4", CYAN, 8.0, 1.4)
    value(sc, x2 + 20, top + 30, "Shadow PvP", TEXT, 22, 0.0)
    # stat rail
    for i, (lab, val) in enumerate((("VERSION", "1.21.10"), ("FABRIC", "0.16.9"),
                                    ("ACTIVE", "42"))):
        sx = x2 + 20 + i * 150
        label(sc, sx, top + 70, lab)
        value(sc, sx, top + 82, val, WHITE, 14, 0.3)
    sc.rect(x2 + 20, top + 110, w2 - 40, 1, base.rgba(WHITE, 22), radius=1)

    # spec block: two columns so the middle of the card is not half empty
    specs = (("RENDERER", "MobileGlues"), ("SHADERS", "Complementary"),
             ("SERVER", "LuciferMC · 24ms"), ("FPS CAP", "Unlimited"),
             ("MODS DIR", "12.4 GB · 42 mods"), ("WORLD", "Lifesteel · day 42"))
    for i, (lab, val) in enumerate(specs):
        col, row = i % 2, i // 2
        yy = top + 122 + row * 28
        xx = x2 + 20 + col * (w2 * 0.30)
        label(sc, xx, yy, lab)
        value(sc, xx + 92, yy - 1, val, TEXT_2, 9.4, 0.2)

    hero_skin(sc, x2 + w2 * 0.735, top + 480 - 66, 320)

    # launch row
    by = top + 480 - 62
    sc.rect(x2 + 20, by - 12, w2 - 40, 1, base.rgba(WHITE, 22), radius=1)
    value(sc, x2 + 20, by + 6, "6.0 GB", WHITE, 15, 0.3)
    gw = sc.width_of("6.0 GB", 15, True, 0.3)
    label(sc, x2 + 24 + gw, by + 12, "RAM ALLOC")
    launch_button(sc, x2 + w2 - 20 - 200, by, 200, 40, "READY TO LAUNCH", 9.2)

    panel(sc, x2, 580, w2, 172, radius=12)
    panel_title(sc, x2, 580, w2, "RECENT WORLDS", "3 WORLDS")
    for i, (nm, sub) in enumerate((("Lifesteel Base", "creative · spawn"),
                                   ("Shadow Arena", "pvp · 1v1"),
                                   ("Dragon Vault", "survival · day 42"))):
        tx = x2 + 14 + i * 226
        sc.rect(tx, 606, 214, 128, base.rgba(PALETTE["panel_hi"], 170), radius=9,
                outline=base.rgba(WHITE, 24), width=1)
        sc.rect(tx + 10, 614, 194, 62, base.rgba(base.lerp(CYAN, PALETTE["panel"], 0.62), 210),
                radius=7, outline=base.rgba(CYAN, 110), width=1)
        sc.poly([(tx + 107, 630), (tx + 130, 645), (tx + 107, 660), (tx + 84, 645)],
                fill=base.rgba(WHITE, 180))
        value(sc, tx + 10, 684, nm, TEXT, 9.4, 0.4)
        label(sc, tx + 10, 700, sub, TEXT_3, 7.2, 0.6)
        chip(sc, tx + 10, 714, "PLAY", size=7.0, accent=CYAN, filled=True, pad=9, h=18)

    # ---- column 3: telemetry / store / keys / new
    x3, w3 = 1152, 428
    panel(sc, x3, top, w3, 120)
    panel_title(sc, x3, top, w3, "LIVE TELEMETRY", "60 FPS", CYAN)
    for i, (lab, val, col) in enumerate((("FRAME", "16.7 ms", TEXT), ("RAM", "6.0 / 8 GB", TEXT))):
        label(sc, x3 + 14 + i * 200, top + 34, lab)
        value(sc, x3 + 14 + i * 200, top + 46, val, col, 13, 0.2)
    sc.rect(x3 + 14, top + 80, w3 - 28, 6, base.rgba(WHITE, 28), radius=3)
    sc.grad_rect(x3 + 14, top + 80, (w3 - 28) * 0.62, 6, base.lerp(CYAN, WHITE, 0.4), CYAN, radius=3)
    label(sc, x3 + 14, top + 94, "VULKAN 1.3 · VSYNC OFF · UNLIMITED")

    panel(sc, x3, 220, w3, 210)
    panel_title(sc, x3, 220, w3, "SHADOW DRAGON ARSENAL", None, MAGENTA)
    value(sc, x3 + 14, 244, "MOD STORE", TEXT, 15, 0.8)
    sc.text(x3 + 14, 268, "Sodium · Iris · packs every week", 8.2, TEXT_3, False, 0.3)
    for i, (m, n) in enumerate((("Sodium Extras", "2.4 MB"), ("Dragon Wings", "8.1 MB"))):
        yy = 288 + i * 32
        sc.rect(x3 + 14, yy, w3 - 28, 26, base.rgba(PALETTE["panel_hi"], 170), radius=7,
                outline=base.rgba(WHITE, 22), width=1)
        sc.text(x3 + 24, yy + 8, m, 8.6, TEXT, True, 0.4)
        sc.text_end(x3 + w3 - 24, yy + 9, n, 7.4, TEXT_3, True, 0.4)
    chip(sc, x3 + 14, 356, "BROWSE STORE", size=7.6, accent=MAGENTA, filled=True, pad=12, h=22)
    chip(sc, x3 + 148, 356, "HUD KEYS", size=7.6, pad=12, h=22)

    panel(sc, x3, 446, w3, 140)
    panel_title(sc, x3, 446, w3, "HUD KEYS", "12 BOUND")
    keys = (("DEBUG", "F3"), ("TAB", "TAB"), ("ZOOM", "C"), ("SIT", "X"), ("3RD", "F5"), ("RAT", "R"))
    for i, (k, v) in enumerate(keys):
        yy = 470 + (i // 3) * 32
        xx = x3 + 14 + (i % 3) * 136
        sc.rect(xx, yy, 124, 26, base.rgba(PALETTE["panel_hi"], 180), radius=7,
                outline=base.rgba(CYAN, 70), width=1)
        sc.text(xx + 10, yy + 8, k, 7.6, TEXT_2, True, 0.9)
        sc.text_end(xx + 114, yy + 8, v, 8.0, CYAN, True, 0.4)

    panel(sc, x3, 602, w3, 150)
    panel_title(sc, x3, 602, w3, "NEW INSTANCE")
    value(sc, x3 + 14, 626, "+ Create", TEXT, 14, 0.4)
    sc.text(x3 + 14, 648, "vanilla · modded · snapshot", 8.0, TEXT_3, False, 0.3)
    chip(sc, x3 + 14, 668, "1.21.10", size=7.4)
    chip(sc, x3 + 90, 668, "FABRIC", size=7.4)
    chip(sc, x3 + 168, 668, "VANILLA", size=7.4)
    launch_button(sc, x3 + 14, 700, w3 - 28, 34, "CREATE INSTANCE", 8.6)

    base.dock(sc, PALETTE)


# --------------------------------------------------------------------------- B · CONSOLE
def variant_b(sc):
    base.header(sc, PALETTE)

    # telemetry strip
    panel(sc, PAD, 84, W - PAD * 2, 38, radius=9)
    tx = PAD + 16
    tx = sc.text(tx, 96, "VULKAN 1.3", 8.6, CYAN, True, 1.0) / S + 14
    tx = sc.text(tx, 96, "·", 9, TEXT_3) / S + 10
    tx = sc.text(tx, 96, "60 FPS", 8.6, TEXT, True, 1.0) / S + 14
    tx = sc.text(tx, 96, "·", 9, TEXT_3) / S + 10
    tx = sc.text(tx, 96, "16.7 ms", 8.6, TEXT, True, 1.0) / S + 14
    tx = sc.text(tx, 96, "·", 9, TEXT_3) / S + 10
    tx = sc.text(tx, 96, "6.0 GB RAM", 8.6, MAGENTA, True, 1.0) / S + 14
    tx = sc.text(tx, 96, "·", 9, TEXT_3) / S + 10
    sc.text(tx, 96, "MOBILEGLUES", 8.6, TEXT_2, True, 1.0)
    sc.text_end(W - PAD - 16, 95, "1.21.10 READY · NO VSYNC", 8.2, OK, True, 0.8)

    # hero
    hx, hy, hw, hh = PAD, 138, 980, 444
    panel(sc, hx, hy, hw, hh, glow=True, radius=14)
    label(sc, hx + 22, hy + 18, "SELECTED INSTANCE", CYAN, 7.8, 1.6)
    value(sc, hx + 22, hy + 32, "Shadow PvP", TEXT, 26, 0.0)
    label(sc, hx + 22, hy + 70, "FABRIC 1.21.4 · 1.21.10 · 42 MODS · COMPLEMENTARY", TEXT_3, 8.2, 1.0)
    sc.rect(hx + 22, hy + 92, hw - 44, 1, base.rgba(WHITE, 22), radius=1)
    for i, (lab, val) in enumerate((("RENDERER", "MobileGlues"), ("SERVER", "LuciferMC · 24ms"),
                                    ("MODS DIR", "12.4 GB"), ("WORLD", "Lifesteel · day 42"),
                                    ("SHADERS", "Complementary"))):
        yy = hy + 108 + i * 24
        label(sc, hx + 22, yy, lab)
        value(sc, hx + 118, yy - 1, val, TEXT_2, 9.6, 0.2)
    hero_skin(sc, hx + hw * 0.74, hy + hh - 96, 268)
    value(sc, hx + 22, hy + hh - 92, "6.0 GB", WHITE, 18, 0.3)
    gw = sc.width_of("6.0 GB", 18, True, 0.3)
    label(sc, hx + 28 + gw, hy + hh - 85, "RAM ALLOCATED")
    launch_button(sc, hx + hw - 22 - 230, hy + hh - 96, 230, 44, "READY TO LAUNCH", 10)

    # right stack
    rx, rw = 1016, W - PAD - 1016
    panel(sc, rx, 138, rw, 154)
    panel_title(sc, rx, 138, rw, "SERVER")
    value(sc, rx + 14, 158, "LUCIFERMC", TEXT, 14, 0.6)
    label(sc, rx + 14, 178, "LIFESTEEL SMP", CYAN, 7.8, 1.2)
    label(sc, rx + 14, 192, "play.lucifermc.fun", TEXT_3, 7.8, 0.3)
    dot(sc, rx + 22, 214, 3.2)
    sc.text(rx + 32, 208, "LIVE · 24ms · 12/200", 8.6, OK, True, 0.4)
    sc.text_end(rx + rw - 14, 208, "OFFICIAL", 7.4, base.lerp(MAGENTA, WHITE, 0.35), True, 1.0)

    panel(sc, rx, 308, rw, 274)
    panel_title(sc, rx, 308, rw, "MY INSTANCES", "4 / 12")
    for i, (t, sub, ver, act) in enumerate((("Fabric 1.21.10", "SHADOW PVP", "1.21.10", True),
                                            ("LuciferMC SMP", "LIFESTEEL", "1.21.4", False),
                                            ("CS Client", "PVP 1.8.9", "1.8.9", False))):
        instance_row(sc, rx + 12, 338 + i * 76, rw - 24, 68, t, sub, ver, active=act)

    # bottom row
    mods_plate(sc, PAD, 598, 980, 74)
    sc.text(PAD + 16, 640, "", 8, TEXT_3)

    panel(sc, rx, 598, rw, 74, radius=12)
    label(sc, rx + 14, 610, "SHADOW DRAGON ARSENAL", MAGENTA, 7.4, 1.2)
    value(sc, rx + 14, 624, "MOD STORE", TEXT, 12, 0.6)
    chip(sc, rx + rw - 110, 616, "BROWSE", size=7.6, accent=MAGENTA, filled=True, pad=11)

    panel(sc, PAD, 688, W - PAD * 2, 122)
    panel_title(sc, PAD, 688, W - PAD * 2, "RECENT WORLDS", "3 WORLDS")
    for i, (nm, sub) in enumerate((("Lifesteel Base", "creative · spawn"), ("Shadow Arena", "pvp · 1v1"),
                                   ("Dragon Vault", "survival · day 42"))):
        tw = 480
        tx = PAD + 14 + i * (tw + 16)
        sc.rect(tx, 714, tw, 80, base.rgba(PALETTE["panel_hi"], 160), radius=9,
                outline=base.rgba(WHITE, 24), width=1)
        sc.rect(tx + 10, 722, 64, 64, base.rgba(base.lerp(CYAN, PALETTE["panel"], 0.6), 220),
                radius=8, outline=base.rgba(CYAN, 140), width=1)
        sc.poly([(tx + 42, 740), (tx + 56, 748), (tx + 42, 756), (tx + 28, 748)],
                fill=base.rgba(WHITE, 190))
        value(sc, tx + 84, 726, nm, TEXT, 10, 0.4)
        label(sc, tx + 84, 744, sub, TEXT_3, 7.4, 0.8)
        chip(sc, tx + tw - 78, 744, "PLAY", size=7.2, accent=CYAN, filled=True, pad=10, h=19)

    base.dock(sc, PALETTE)


# --------------------------------------------------------------------------- C · CARD DECK
def variant_c(sc):
    base.header(sc, PALETTE)

    # hero left, quick stats right
    hx, hy, hw, hh = PAD, 84, 980, 300
    panel(sc, hx, hy, hw, hh, glow=True, radius=14)
    label(sc, hx + 22, hy + 18, "FABRIC 1.21.4", CYAN, 8.0, 1.5)
    value(sc, hx + 22, hy + 32, "Shadow PvP", TEXT, 24, 0.0)
    for i, (lab, val) in enumerate((("VERSION", "1.21.10"), ("FABRIC", "0.16.9"),
                                    ("MODS", "42"), ("SHADERS", "Comp."))):
        sx = hx + 22 + i * 150
        label(sc, sx, hy + 74, lab)
        value(sc, sx, hy + 86, val, WHITE, 13, 0.3)
    label(sc, hx + 22, hy + 126, "MOBILEGLUES · LUCIFERMC · 24MS · 12.4 GB MODS", TEXT_3, 8.0, 0.9)
    hero_skin(sc, hx + hw * 0.74, hy + hh - 34, 210)
    launch_button(sc, hx + 22, hy + hh - 62, 210, 40, "READY TO LAUNCH", 9.2)
    value(sc, hx + 250, hy + hh - 56, "6.0 GB", WHITE, 16, 0.3)
    gw = sc.width_of("6.0 GB", 16, True, 0.3)
    label(sc, hx + 254 + gw, hy + hh - 50, "RAM ALLOC")

    rx, rw = 1016, W - PAD - 1016
    panel(sc, rx, 84, rw, 146)
    panel_title(sc, rx, 84, rw, "LIVE TELEMETRY", "60 FPS")
    for i, (lab, val) in enumerate((("FRAME TIME", "16.7 ms"), ("RAM", "6.0 / 8 GB"))):
        label(sc, rx + 14, 106 + i * 34, lab)
        value(sc, rx + 122, 104 + i * 34, val, WHITE, 11.5, 0.2)
    sc.rect(rx + 14, 190, rw - 28, 6, base.rgba(WHITE, 28), radius=3)
    sc.grad_rect(rx + 14, 190, (rw - 28) * 0.62, 6, base.lerp(CYAN, WHITE, 0.4), CYAN, radius=3)

    panel(sc, rx, 246, rw, 138)
    panel_title(sc, rx, 246, rw, "SERVER")
    value(sc, rx + 14, 266, "LUCIFERMC", TEXT, 13, 0.6)
    label(sc, rx + 14, 284, "LIFESTEEL SMP · 24ms", OK, 7.8, 0.6)
    label(sc, rx + 14, 300, "play.lucifermc.fun", CYAN, 7.8, 0.3)
    chip(sc, rx + 14, 322, "JOIN", size=7.4, accent=CYAN, filled=True, pad=14)
    chip(sc, rx + 82, 322, "12 / 200", size=7.4, pad=10)

    # deck
    label(sc, PAD, 404, "INSTANCE DECK")
    sc.text_end(W - PAD, 404, "4 OF 12 · SWIPE", 7.4, TEXT_3, True, 1.0)
    tile_w = (W - PAD * 2 - 2 * 16) / 3
    for i, (t, sub, meta, act) in enumerate((
            ("Fabric 1.21.10", "SHADOW PVP · READY", "1.21.10 · 42 MODS", True),
            ("LuciferMC SMP", "LIFESTEEL · ONLINE", "1.21.4 · 24MS", False),
            ("CS Client", "PVP · 1.8.9", "1.8.9 · 12 MODS", False))):
        x = PAD + i * (tile_w + 16)
        y, h = 424, 234
        panel(sc, x, y, tile_w, h, glow=act, radius=12)
        if act:
            sc.rect(x, y, tile_w, h, None, radius=12, outline=base.rgba(CYAN, 220), width=1.6)
        # thumbnail
        sc.rect(x + 14, y + 14, tile_w - 28, 118, base.rgba(base.lerp(CYAN, PALETTE["panel"], 0.62), 210),
                radius=9, outline=base.rgba(CYAN, 120), width=1)
        # horizon + ground band, so the thumbnail reads as a world and not an empty plate
        sc.rect(x + 18, y + 74, tile_w - 36, 54, base.rgba(base.lerp(PALETTE["panel_hi"], CYAN, 0.10), 220),
                radius=7)
        sc.rect(x + 18, y + 72, tile_w - 36, 4, base.rgba(CYAN, 120), radius=2)
        for gx in range(4):
            sc.rect(x + 30 + gx * 46, y + 88 + (gx % 2) * 10, 22, 6,
                    base.rgba(WHITE, 26), radius=2)
        k = 34
        cxm, cym = x + tile_w / 2, y + 62
        sc.poly([(cxm, cym - k * 0.8), (cxm + k, cym - k * 0.18), (cxm, cym + k * 0.46),
                 (cxm - k, cym - k * 0.18)], fill=base.rgba(WHITE, 150))
        sc.poly([(cxm, cym + k * 0.46), (cxm + k, cym - k * 0.18), (cxm + k, cym + k * 0.3),
                 (cxm, cym + k * 0.94)], fill=base.rgba(base.lerp(CYAN, (0, 0, 0), 0.35), 170))
        value(sc, x + 16, y + 146, t, TEXT, 12, 0.4)
        label(sc, x + 16, y + 166, sub, TEXT_3, 7.4, 0.9)
        sc.rect(x + 16, y + 186, tile_w - 32, 1, base.rgba(WHITE, 22), radius=1)
        label(sc, x + 16, y + 196, meta, CYAN, 7.4, 1.0)
        if act:
            dot(sc, x + tile_w - 24, y + 24, 3.4, CYAN)
        else:
            chip(sc, x + tile_w - 76, y + 192, "PLAY", size=7.2, accent=CYAN, pad=12, h=20)

    # bottom band
    mods_plate(sc, PAD, 678, 980, 60)
    panel(sc, rx, 678, rw, 60, radius=30)
    label(sc, rx + 16, 698, "NEW INSTANCE")
    chip(sc, rx + rw - 128, 688, "+ CREATE", size=7.6, accent=CYAN, filled=True, pad=14, h=24)

    panel(sc, PAD, 754, W - PAD * 2, 56, radius=28)
    label(sc, PAD + 16, 774, "SHADOW DRAGON ARSENAL", MAGENTA, 7.4, 1.2)
    sc.text(PAD + 236, 773, "MOD STORE · HUD KEYS · CONTROL PRESETS", 8.2, TEXT_3, True, 0.8)
    chip(sc, W - PAD - 320, 764, "OPEN STORE", size=7.4, accent=MAGENTA, filled=True, pad=12, h=22)
    chip(sc, W - PAD - 200, 764, "HUD KEYS", size=7.4, pad=12, h=22)
    chip(sc, W - PAD - 96, 764, "PRESETS", size=7.4, pad=12, h=22)

    base.dock(sc, PALETTE)


VARIANTS = [
    ("a", "a-hud-clean", "A · HUD CLEAN", "three columns · one baseline grid", variant_a),
    ("b", "b-console", "B · CONSOLE", "telemetry strip · big hero · right stack", variant_b),
    ("c", "c-card-deck", "C · CARD DECK", "hero + horizontal instance deck", variant_c),
]


def render(fn):
    sc = base.Screen(base.build_bg(PALETTE))
    fn(sc)
    sc.finish()
    return sc.img.convert("RGB").resize((W, H), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) or None
    for key, slug, _name, _note, fn in VARIANTS:
        if only and key not in only and slug not in only:
            continue
        img = render(fn)
        img.save(OUT / f"{slug}.png")
        print("wrote", (OUT / f"{slug}.png").relative_to(ROOT), img.size)


if __name__ == "__main__":
    main()
