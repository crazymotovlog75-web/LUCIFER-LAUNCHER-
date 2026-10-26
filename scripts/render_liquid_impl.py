#!/usr/bin/env python3
"""Renders EXACTLY the Liquid Crystal layout that ships in v3.5 (L03 side rail).

Unlike the mockup batch, this follows the real Android layout: the rail carries eight
destinations (HOME … SCENE, SETTINGS), the header pill holds brand + cursor/about/PRO chips +
live telemetry + account + gear, the hero card is the instance, the right column is server →
instances → shortcuts, and the bottom strip is TOP MODS.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import render_liquid_glass as glass  # noqa: E402
from render_liquid_glass import (  # noqa: E402
    CYAN, MAGENTA, WHITE, INK, OK_GREEN, TEXT_2, TEXT_3, rgba, lerp,
)

W, H, PAD, S = 1600, 900, 22, 2

RAIL_ITEMS = ("HOME", "PROFILES", "MODS", "SERVERS", "CONTROLS", "SKINS", "SCENE", "SETTINGS")


class ImplScene(glass.LiquidScreen):
    def glyph_id(self, name):
        if name == "SCENE":
            return "skins"
        return super().glyph_id(name)


def build(sc):
    # ── glass rail ────────────────────────────────────────────────────────
    rail_w = 108
    sc.liquid(PAD, PAD, rail_w, H - PAD * 2, radius=34, tint=72, scrim=92, magnify=0.02)
    sc.avatar(PAD + rail_w / 2, PAD + 34, 17)
    sc.rect(PAD + 18, PAD + 58, rail_w - 36, 1.1, rgba(WHITE, 54), radius=1)

    top = PAD + 70
    step = (H - PAD * 2 - (top - PAD) - 14) / len(RAIL_ITEMS)
    for i, name in enumerate(RAIL_ITEMS):
        cy = top + step * (i + 0.5)
        on = i == 0
        if on:
            sc.rect(PAD + 9, cy - step / 2 + 3, rail_w - 18, step - 6, rgba(WHITE, 64), radius=16,
                    outline=rgba(WHITE, 190), width=1.2)
            sc.rect(PAD + 4, cy - 13, 3.4, 26, rgba(CYAN, 255), radius=2)
        sc.glyph(sc.glyph_id(name), PAD + rail_w / 2, cy - 7, 15,
                 WHITE if on else TEXT_3)
        sc.smid(PAD + rail_w / 2, cy + 12, name, 6.2, WHITE if on else TEXT_3, True, 0.8)

    # ── header pill ───────────────────────────────────────────────────────
    hx, hy, hh = PAD + rail_w + 8, PAD, 54
    hw = W - PAD - hx
    sc.liquid(hx, hy, hw, hh, radius=27, tint=60, scrim=72, magnify=0.03)
    sc.avatar(hx + 26, hy + hh / 2, 15)
    sc.stext(hx + 48, hy + 14, "LUCIFER", 12.5, WHITE, True, 1.6)
    sc.stext(hx + 48, hy + 31, "LIQUID CRYSTAL CLEAR", 6.4, TEXT_3, True, 1.4)

    # nav chips (cursor / about / pro)
    chip_x = hx + 168
    for label, icon in (("Cursor", "controls"), ("", "settings"), ("✦ PRO", "")):
        tw = sc.width_of(label, 7.4, True, 0.5) if label else 0
        cw = tw + (34 if label else 26)
        sc.pill(chip_x, hy + 15, cw, 24, fill=WHITE, alpha=40, edge=rgba(WHITE, 150))
        if icon == "cursor":
            sc.glyph("controls", chip_x + 13, hy + 27, 9, TEXT_2)
        if icon == "about":
            sc.glyph("settings", chip_x + cw / 2, hy + 27, 9, TEXT_2)
        if label:
            sc.text(chip_x + (24 if icon else 10), hy + 21, label, 7.4, TEXT_2, True, 0.5)
        chip_x += cw + 6

    # live telemetry
    tele = "MobileGlues   ·   1.21+ FPS PACK   ·   6.0 GB RAM"
    tele_w = sc.width_of(tele, 7.6, True, 0.4) + 26
    tele_x = hx + hw - 26 - 112 - 8 - 30 - tele_w
    sc.pill(tele_x, hy + 14, tele_w, 26, fill=WHITE, alpha=40, edge=rgba(WHITE, 150))
    sc.text(tele_x + 13, hy + 21, "MobileGlues", 7.6, CYAN, True, 0.4)
    rest = tele_x + 13 + sc.width_of("MobileGlues   ", 7.6, True, 0.4)
    sc.text(rest - 4, hy + 21, "·", 8, MAGENTA, True, 0)
    sc.text(rest + 6, hy + 21, "1.21+ FPS PACK", 7.6, TEXT_2, True, 0.4)
    rest += 6 + sc.width_of("1.21+ FPS PACK   ", 7.6, True, 0.4)
    sc.text(rest - 4, hy + 21, "·", 8, MAGENTA, True, 0)
    sc.text(rest + 6, hy + 21, "6.0 GB RAM", 7.6, WHITE, True, 0.4)

    # account + gear
    acc_x = hx + hw - 26 - 112
    sc.pill(acc_x, hy + 14, 112, 26, fill=WHITE, alpha=44, edge=rgba(WHITE, 160))
    sc.avatar(acc_x + 15, hy + 27, 9)
    sc.text(acc_x + 28, hy + 20, "SAIFKHAN", 7.6, WHITE, True, 0.5)
    sc.text(acc_x + 28, hy + 30, "SHADOW DRAGON", 5.8, TEXT_3, True, 0.5)
    sc.pill(hx + hw - 36, hy + 14, 26, 26, fill=WHITE, alpha=40, edge=rgba(WHITE, 150))
    sc.glyph("settings", hx + hw - 23, hy + 27, 10, WHITE)

    # ── content ───────────────────────────────────────────────────────────
    cx0 = hx
    cw_all = W - PAD - cx0
    ctop = PAD + hh + 8
    strip_h, strip_gap = 44, 8
    cbot = H - PAD - strip_h - strip_gap

    hero_w = (cw_all - 10) * 0.62
    hx0 = cx0
    sc.liquid(hx0, ctop, hero_w, cbot - ctop, radius=30, tint=84, scrim=78, magnify=0.06)

    sc.stext(hx0 + 22, ctop + 16, "FABRIC 1.21.4", 7.6, CYAN, True, 1.4)
    sc.stext(hx0 + 22, ctop + 30, "Shadow PvP", 17, WHITE, True, 0.2)

    sy = ctop + 66
    for i, (lab, val) in enumerate((("VERSION", "1.21.10"), ("FABRIC", "0.16.9"), ("ACTIVE", "42 mods"))):
        bx = hx0 + 22 + i * 118
        sc.stext(bx, sy, lab, 6.6, TEXT_3, True, 1.1)
        sc.stext(bx, sy + 13, val, 13, WHITE, True, 0.2)

    ry = sy + 46
    for i, (lab, val) in enumerate((("RENDERER", "MobileGlues"), ("SHADERPACKS", "3 packs"),
                                    ("SERVER", "LuciferMC · 24 ms"))):
        yy = ry + i * 20
        sc.text(hx0 + 22, yy, lab, 6.6, TEXT_3, True, 1.2)
        sc.stext(hx0 + 96, yy - 1, val, 9.2, WHITE, True, 0.2)

    # skin preview
    sprite = glass.base.skin_sprite(scale=12)
    th = 300
    tw = th * sprite.width / sprite.height
    px = hx0 + hero_w - 40 - tw
    sc.halo(px + tw / 2, ctop + 340, tw * 0.6, CYAN, 40)
    img = sprite.resize((int(tw * S), int(th * S)), Image.LANCZOS)
    sc.img.alpha_composite(img, (sc.s(px), sc.s(ctop + 150)))
    sc.redraw()

    # RAM + launch + skin studio
    by = cbot - 56
    sc.stext(hx0 + 22, by, "6.0 GB", 13, WHITE, True, 0.3)
    sc.stext(hx0 + 22 + sc.width_of("6.0 GB", 13, True, 0.3) + 8, by + 4, "RAM ALLOC", 6.6, TEXT_3, True, 1.1)
    bw = 190
    sc.grad_rect(hx0 + hero_w - 22 - bw, by - 8, bw, 34, lerp(CYAN, WHITE, 0.5), CYAN, radius=17)
    sc.glyph("play", hx0 + hero_w - 22 - bw + 26, by + 9, 9, INK, 1.4)
    sc.text(hx0 + hero_w - 22 - bw + 44, by + 2, "READY TO LAUNCH", 8.6, INK, True, 0.8)
    sc.text_end(hx0 + hero_w - 22, by + 22, "1.21.10 · 42 MODS · MOBILEGLUES", 6.2, TEXT_3, True, 0.5)
    sc.pill(hx0 + 22, cbot - 92, 116, 24, fill=WHITE, alpha=44, edge=rgba(WHITE, 160))
    sc.text(hx0 + 36, cbot - 86, "✦ SKIN STUDIO", 7.2, WHITE, True, 0.9)

    # ── right column ──────────────────────────────────────────────────────
    rx = cx0 + hero_w + 10
    rw = W - PAD - rx

    server_h = 150
    sc.liquid(rx, ctop, rw, server_h, radius=26, tint=68, scrim=90, magnify=0.05)
    sc.stext(rx + 18, ctop + 16, "LUCIFERMC", 12, WHITE, True, 1.2)
    sc.pill(rx + rw - 90, ctop + 12, 72, 20, fill=WHITE, alpha=48, edge=rgba(WHITE, 170))
    sc.text_mid(rx + rw - 54, ctop + 18, "OFFICIAL", 6.2, WHITE, True, 0.8)
    sc.stext(rx + 18, ctop + 34, "LIFESTEEL SMP", 6.6, TEXT_3, True, 1.2)
    sc.text(rx + 18, ctop + 54, "PLAYERS", 6.4, TEXT_3, True, 1.2)
    sc.text_end(rx + rw - 18, ctop + 54, "12 / 200", 7.8, TEXT_2, True, 0.4)
    sc.pill(rx + 18, ctop + 70, rw - 36, 22, fill=WHITE, alpha=38, edge=rgba(WHITE, 130))
    sc.text(rx + 30, ctop + 76, "play.lucifermc.fun", 7.4, CYAN, True, 0.3)
    sc.dot(rx + rw - 118, ctop + 81, 3.0, OK_GREEN)
    sc.text(rx + rw - 108, ctop + 76, "LIVE · 24ms", 7.4, OK_GREEN, True, 0.5)
    bw3 = (rw - 36 - 12) / 3
    for i, (lab, on) in enumerate((("JOIN", True), ("DISCORD", False), ("WIKI", False))):
        bx = rx + 18 + i * (bw3 + 6)
        if on:
            sc.grad_rect(bx, ctop + 102, bw3, 24, lerp(CYAN, WHITE, 0.5), CYAN, radius=12)
            sc.text_mid(bx + bw3 / 2, ctop + 108, lab, 7.6, INK, True, 1.0)
        else:
            sc.pill(bx, ctop + 102, bw3, 24, fill=WHITE, alpha=44, edge=rgba(WHITE, 160))
            sc.text_mid(bx + bw3 / 2, ctop + 108, lab, 7.6, WHITE, True, 0.9)

    inst_y = ctop + server_h + 10
    inst_h = cbot - inst_y - 44
    sc.liquid(rx, inst_y, rw, inst_h, radius=26, tint=68, scrim=90, magnify=0.05)
    sc.stext(rx + 18, inst_y + 14, "INSTANCES", 7.6, TEXT_3, True, 1.4)
    sc.pill(rx + rw - 66, inst_y + 9, 48, 19, fill=WHITE, alpha=44, edge=rgba(WHITE, 150))
    sc.text_mid(rx + rw - 42, inst_y + 14, "ALL ›", 6.8, WHITE, True, 0.6)

    row_y = inst_y + 38
    for i, (nm, sub) in enumerate((("Fabric 1.21.10", "SHADOW PVP · CURRENT"),
                                   ("LuciferMC SMP", "LIFESTEEL · ONLINE"),
                                   ("CS Client", "PVP · 1.8.9"))):
        yy = row_y + i * 58
        on = i == 0
        sc.rect(rx + 16, yy, rw - 32, 50, rgba(WHITE, 66 if on else 40), radius=14,
                outline=rgba(CYAN if on else WHITE, 200 if on else 110), width=1.1)
        sc.glyph("servers", rx + 34, yy + 25, 10, CYAN if on else TEXT_3)
        sc.text(rx + 50, yy + 12, nm, 9.4, WHITE, True, 0.4)
        sc.text(rx + 50, yy + 28, sub, 6.8, TEXT_3, True, 0.7)
        sc.glyph("play", rx + rw - 32, yy + 25, 9, CYAN if on else TEXT_2)

    btn_y = inst_y + inst_h - 34
    bw4 = (rw - 32 - 8 - 26) / 2
    sc.pill(rx + 16, btn_y, bw4, 24, fill=WHITE, alpha=44, edge=rgba(WHITE, 155))
    sc.text_mid(rx + 16 + bw4 / 2, btn_y + 7, "＋ NEW", 7.4, WHITE, True, 0.9)
    sc.pill(rx + 16 + bw4 + 4, btn_y, bw4, 24, fill=WHITE, alpha=44, edge=rgba(WHITE, 155))
    sc.text_mid(rx + 16 + bw4 + 4 + bw4 / 2, btn_y + 7, "MODS DIR", 7.4, WHITE, True, 0.9)
    sc.pill(rx + 16 + (bw4 + 4) * 2, btn_y, 26, 24, fill=WHITE, alpha=44, edge=rgba(WHITE, 155))
    sc.text_mid(rx + 16 + (bw4 + 4) * 2 + 13, btn_y + 6, "↻", 8.6, WHITE, True, 0)

    sk_y = cbot - 38
    bw5 = (rw - 6) / 2
    sc.pill(rx, sk_y, bw5, 26, fill=WHITE, alpha=44, edge=rgba(WHITE, 160))
    sc.text_mid(rx + bw5 / 2, sk_y + 8, "⚡ MOD STORE", 7.4, WHITE, True, 0.9)
    sc.pill(rx + bw5 + 6, sk_y, bw5, 26, fill=WHITE, alpha=44, edge=rgba(WHITE, 160))
    sc.text_mid(rx + bw5 + 6 + bw5 / 2, sk_y + 8, "⌨ HUD KEYS", 7.4, WHITE, True, 0.9)

    # ── bottom strip: TOP MODS ────────────────────────────────────────────
    sc.liquid(cx0, H - PAD - strip_h, cw_all, strip_h, radius=22, tint=60, scrim=76, magnify=0.03)
    sc.stext(cx0 + 18, H - PAD - strip_h + 14, "TOP MODS", 6.6, TEXT_3, True, 1.4)
    mx = cx0 + 82
    for name in ("Sodium", "Iris", "Lithium", "Krypton", "Ferrite"):
        tw2 = sc.width_of(name, 7.2, True, 0.4) + 18
        sc.pill(mx, H - PAD - strip_h + 11, tw2, 22, fill=WHITE, alpha=46, edge=rgba(WHITE, 165))
        sc.text(mx + 9, H - PAD - strip_h + 17, name, 7.2, WHITE, True, 0.4)
        mx += tw2 + 6
    sc.text_end(W - PAD - 18, H - PAD - strip_h + 14, "42 ACTIVE", 7.2, WHITE, True, 1.0)


def main():
    glass.W, glass.H, glass.S = W, H, S
    scene = ImplScene(glass.build_bg())
    build(scene)
    scene.finish()

    out = ROOT / "mockups" / "variants" / "liquid" / "shipped" / "v35-liquid-crystal.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    full = scene.img.convert("RGB")
    full.save(out, "PNG")
    print(f"{out.relative_to(ROOT)}  {full.size}")

    jpg = out.with_suffix(".jpg")
    full.resize((1280, 720), Image.LANCZOS).save(
        jpg, "JPEG", quality=88, optimize=True, progressive=True)
    print(f"{jpg.relative_to(ROOT)}  {jpg.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
