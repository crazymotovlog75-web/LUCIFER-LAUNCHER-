#!/usr/bin/env python3
"""10 launcher home-screen layouts in the iOS 26 "Liquid Glass" look.

Same crystal-clear glass on every sheet (clear refraction, chromatic fringe, specular rim,
squircle corners), only the layout changes so the pick is about structure, not colour.

Run:  python3 scripts/render_liquid_glass.py [l01 l05 ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import render_launcher_screens as base

ROOT = Path(__file__).resolve().parent.parent
MOCK = ROOT / "mockups"
OUT = MOCK / "variants" / "liquid"
WALL = MOCK / "backgrounds" / "bg10-abyss-teal.jpg"
SKIN = MOCK / "assets" / "skin-default.png"

W, H = 1600, 900
S = 2
PAD = 22

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

rgba = base.rgba
lerp = base.lerp
vgrad = base.vgrad
rounded_mask = base.rounded_mask

# ---- brand tokens -----------------------------------------------------------
CYAN = (47, 233, 255)
MAGENTA = (217, 70, 239)
WHITE = (255, 255, 255)
INK = (8, 16, 22)
TEXT = (255, 255, 255)
TEXT_2 = (216, 236, 245)
TEXT_3 = (168, 196, 208)
OK_GREEN = (52, 211, 153)
AMBER = (255, 196, 107)

DOCK = ["HOME", "PROFILES", "MODS", "SERVERS", "CONTROLS", "SKINS", "SETTINGS"]
MODS = ["Sodium", "Iris", "Lithium", "Krypton", "Ferrite"]


# --------------------------------------------------------------------------- background
def build_bg():
    """BG10 Abyss Teal, lifted into a bright vivid wash so clear glass has something to bend."""
    art = Image.open(WALL).convert("RGB")
    art = ImageOps.fit(art, (W * S, H * S), method=Image.LANCZOS)
    art = ImageEnhance.Brightness(art).enhance(1.52)
    art = ImageEnhance.Color(art).enhance(1.62)
    art = ImageEnhance.Contrast(art).enhance(1.04)

    glow = Image.new("RGBA", art.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for fx, fy, fr, col, a in (
        (0.18, 0.14, 0.30, (0, 236, 255), 120),
        (0.82, 0.18, 0.26, (255, 90, 214), 105),
        (0.50, 0.86, 0.34, (0, 150, 220), 80),
        (0.68, 0.55, 0.20, (150, 250, 255), 70),
    ):
        gd.ellipse([art.size[0] * (fx - fr), art.size[1] * (fy - fr),
                    art.size[0] * (fx + fr), art.size[1] * (fy + fr)], fill=rgba(col, a))
    glow = glow.filter(ImageFilter.GaussianBlur(art.size[0] // 8))
    art = Image.alpha_composite(art.convert("RGBA"), glow)

    # a soft top light so the specular rims have something to answer to
    top = Image.new("RGBA", art.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    for y in range(art.size[1]):
        t = y / (art.size[1] - 1)
        td.line([(0, y), (art.size[0], y)], fill=rgba((255, 255, 255), int(46 * (1 - t) ** 2)))
    return Image.alpha_composite(art, top)


# --------------------------------------------------------------------------- helpers
def alpha_grad(size, top_a, bottom_a, color=WHITE):
    w, h = size
    col = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        col.putpixel((0, y), rgba(color, int(top_a + (bottom_a - top_a) * t)))
    return col.resize((w, h), Image.BILINEAR)


def shape_mask(size, radius):
    return rounded_mask(size, max(0, int(radius)))


class LiquidScreen(base.Screen):
    """The base Screen plus the liquid-glass panel."""

    # ---- the glass ------------------------------------------------------
    def liquid(self, x, y, w, h, radius=26, tint=30, scrim=62, magnify=0.055,
               accent=CYAN, shadow=96, rim=1.0, spec=1.0, edge_col=WHITE):
        box = self.box(x, y, w, h)
        pw, ph = self.s(w), self.s(h)
        r = self.s(radius)

        # 1. soft lift
        sh = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [box[0], box[1] + self.s(2), box[2], box[3] + self.s(9)], r,
            fill=(0, 0, 0, int(shadow)))
        self.img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(self.s(12))))
        self.redraw()

        # 2. refraction: a slightly wider crop squeezed through the pane, so the wallpaper
        #    bends near the rim exactly like a real lens
        mx, my = int(pw * (1 + magnify)), int(ph * (1 + magnify))
        ox, oy = box[0] + (pw - mx) // 2, box[1] + (ph - my) // 2
        crop = self.img.crop((ox, oy, ox + mx, oy + my))
        refr = crop.resize((pw, ph), Image.LANCZOS)
        refr = refr.convert("RGB")
        refr = ImageEnhance.Brightness(refr).enhance(1.06)
        refr = ImageEnhance.Color(refr).enhance(1.20)
        refr = ImageEnhance.Contrast(refr).enhance(1.02)

        # chromatic dispersion: the red and blue planes split by a hair at the edges
        ch_r, ch_g, ch_b = refr.split()
        ch_r = ImageChops.offset(ch_r, self.s(1.4), 0)
        ch_b = ImageChops.offset(ch_b, -self.s(1.4), 0)
        refr = Image.merge("RGB", (ch_r, ch_g, ch_b))
        refr = refr.filter(ImageFilter.GaussianBlur(self.s(0.7)))

        mask = shape_mask((pw, ph), r)
        refr = refr.convert("RGBA")
        refr.putalpha(mask)
        self.img.alpha_composite(refr, (box[0], box[1]))
        self.redraw()

        # 3. white tint: strong at the top edge, thin at the bottom
        tintimg = alpha_grad((pw, ph), int(tint * 1.25), int(tint * 0.35))
        tintimg.putalpha(ImageChops.multiply(tintimg.split()[3], mask))
        self.img.alpha_composite(tintimg, (box[0], box[1]))

        # 4. bottom scrim so labels stay readable on a bright wallpaper
        if scrim > 0:
            sc = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sc)
            sd.rectangle([0, int(ph * 0.34), pw, ph], fill=(0, 0, 0, int(scrim)))
            sc = sc.filter(ImageFilter.GaussianBlur(self.s(14)))
            sc.putalpha(ImageChops.multiply(sc.split()[3], mask))
            self.img.alpha_composite(sc, (box[0], box[1]))
        self.redraw()

        # 5. specular sweep across the top third
        if spec > 0:
            shn = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(shn).polygon(
                [(0, 0), (pw, 0), (pw, int(ph * 0.16)), (0, int(ph * 0.34))],
                fill=rgba(WHITE, int(34 * spec)))
            shn = shn.filter(ImageFilter.GaussianBlur(self.s(10)))
            shn.putalpha(ImageChops.multiply(shn.split()[3], mask))
            self.img.alpha_composite(shn, (box[0], box[1]))
            self.redraw()

        # 6. the lens rim: three hairlines, bright outside, softer inside
        if rim > 0:
            for i, (inset, a, wd) in enumerate(((0, 235, 2.0), (1.6, 150, 1.4), (3.4, 80, 1.2))):
                self.d.rounded_rectangle(
                    [box[0] + self.s(inset), box[1] + self.s(inset),
                     box[2] - self.s(inset), box[3] - self.s(inset)],
                    max(1, r - self.s(inset)),
                    outline=rgba(edge_col, int(a * rim)), width=max(1, self.s(wd)))
            # bottom inner shade = thickness of the glass
            self.d.arc([box[0] - r * 0.1, box[1] + ph * 0.55, box[2] + r * 0.1, box[3] + ph * 0.20],
                       start=18, end=162, fill=rgba((0, 0, 0), 46), width=self.s(3))

        # 7. crisp top refraction line + a corner glint
        if rim > 0:
            self.d.line([(self.s(x + radius * 0.55), self.s(y + 1.2)),
                         (self.s(x + w - radius * 0.55), self.s(y + 1.2))],
                        fill=rgba(WHITE, int(224 * rim)), width=max(2, self.s(1.5)))
            gx, gy = x + radius * 0.55, y + h * 0.16
            gl = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).ellipse([self.s(gx - w * 0.055), self.s(gy - h * 0.10),
                                        self.s(gx + w * 0.055), self.s(gy + h * 0.10)],
                                       fill=rgba(WHITE, 52))
            self.img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(self.s(9))))
            self.redraw()

        # 8. whisper of accent light on the outer edge
        self.halo(x + w / 2, y + h * 0.02, w * 0.44, accent, 16, blur=self.s(14))

    # ---- text with a shadow, for glass ---------------------------------
    def stext(self, x, y, s, size, color=TEXT, bold=True, track=0.0, shadow=130):
        self.text(x + 0.7, y + 0.8, s, size, (0, 0, 0, shadow), bold, track)
        self.text(x, y, s, size, color, bold, track)

    def smid(self, cx, y, s, size, color=TEXT, bold=True, track=0.0, shadow=130):
        self.text_mid(cx + 0.7, y + 0.8, s, size, (0, 0, 0, shadow), bold, track)
        self.text_mid(cx, y, s, size, color, bold, track)

    def send(self, rx, y, s, size, color=TEXT, bold=True, track=0.0, shadow=130):
        self.text_end(rx + 0.7, y + 0.8, s, size, (0, 0, 0, shadow), bold, track)
        self.text_end(rx, y, s, size, color, bold, track)

    # ---- small components ----------------------------------------------
    def pill(self, x, y, w, h, fill=WHITE, alpha=46, edge=WHITE, edge_alpha=150, radius=None):
        radius = h / 2 if radius is None else radius
        self.rect(x, y, w, h, rgba(fill, alpha), radius=radius,
                  outline=rgba(edge, edge_alpha), width=1.2)
        self.rect(x + 1, y + 1, w - 2, max(1, h * 0.42), rgba(WHITE, 26), radius=max(1, radius - 1))

    def chip(self, x, y, label, size=8.5, active=False, accent=CYAN, pad=11, h=22):
        tw = self.width_of(label, size, True, 0.6)
        w = tw + pad * 2
        if active:
            self.grad_rect(x, y, w, h, lerp(accent, WHITE, 0.55), accent, radius=h / 2)
            self.text_mid(x + w / 2, y + (h - size * 1.05) / 2, label, size, INK, True, 0.6)
        else:
            self.pill(x, y, w, h)
            self.text_mid(x + w / 2, y + (h - size * 1.05) / 2, label, size, TEXT_2, True, 0.6)
        return w

    def stat_block(self, x, y, label, value, w=None, accent=CYAN, size=15):
        self.stext(x, y, label, 7.4, TEXT_3, True, 1.1)
        self.stext(x, y + 13, value, size, accent, True, 0.2)

    def avatar(self, cx, cy, r, accent=CYAN):
        sprite = base.skin_sprite(scale=8)
        head = sprite.crop((32, 0, 96, 64)).resize((self.s(r * 2), self.s(r * 2)), Image.LANCZOS)
        mask = Image.new("L", head.size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, head.size[0] - 1, head.size[1] - 1], fill=255)
        disc = Image.new("RGBA", head.size, (0, 0, 0, 0))
        disc.alpha_composite(head)
        disc.putalpha(mask)
        self.img.alpha_composite(disc, (self.s(cx - r), self.s(cy - r)))
        self.redraw()
        self.d.ellipse([self.s(cx - r), self.s(cy - r), self.s(cx + r), self.s(cy + r)],
                       outline=rgba(WHITE, 200), width=max(2, self.s(1.6)))
        self.halo(cx, cy, r * 1.5, accent, 34)

    def badge(self, x, y, label, color=OK_GREEN, size=7.6):
        tw = self.width_of(label, size, True, 0.7)
        self.pill(x, y, tw + 20, 18, fill=color, alpha=210, edge=WHITE, edge_alpha=120)
        self.text_mid(x + (tw + 20) / 2, y + 5.2, label, size, (6, 22, 16), True, 0.7)

    def dot(self, cx, cy, r, color, glow=True):
        self.ellipse(cx - r, cy - r, r * 2, r * 2, fill=color)
        if glow:
            self.halo(cx, cy, r * 3.2, color, 90)

    def glyph(self, kind, cx, cy, s, color=TEXT_2, width=1.7, filled=False):
        c = rgba(color)
        if kind == "home":
            self.poly([(cx - s * 0.52, cy + s * 0.04), (cx, cy - s * 0.56), (cx + s * 0.52, cy + s * 0.04)],
                      fill=c if filled else None, outline=c, width=width)
            self.rect(cx - s * 0.33, cy + s * 0.02, s * 0.66, s * 0.48,
                      c if filled else None, radius=2, outline=c, width=width)
        elif kind == "profiles":
            self.ellipse(cx - s * 0.23, cy - s * 0.52, s * 0.46, s * 0.46, fill=c)
            self.poly([(cx - s * 0.5, cy + s * 0.5), (cx - s * 0.34, cy - s * 0.02),
                       (cx + s * 0.34, cy - s * 0.02), (cx + s * 0.5, cy + s * 0.5)], fill=c)
        elif kind == "mods":
            for i in range(3):
                self.rect(cx - s * 0.46, cy - s * 0.46 + i * s * 0.34, s * 0.92, s * 0.2,
                          c, radius=2.4)
        elif kind == "servers":
            self.rect(cx - s * 0.46, cy - s * 0.48, s * 0.92, s * 0.38, None, radius=3, outline=c, width=width)
            self.rect(cx - s * 0.46, cy + s * 0.06, s * 0.92, s * 0.38, None, radius=3, outline=c, width=width)
            self.dot(cx - s * 0.28, cy - s * 0.29, s * 0.07, color, glow=False)
            self.dot(cx - s * 0.28, cy + s * 0.25, s * 0.07, color, glow=False)
        elif kind == "controls":
            self.rect(cx - s * 0.14, cy - s * 0.5, s * 0.28, s * 1.0, c, radius=3)
            self.rect(cx - s * 0.5, cy - s * 0.14, s * 1.0, s * 0.28, c, radius=3)
        elif kind == "skins":
            self.poly([(cx - s * 0.30, cy - s * 0.44), (cx - s * 0.52, cy - s * 0.16),
                       (cx - s * 0.30, cy - s * 0.02), (cx - s * 0.30, cy + s * 0.5),
                       (cx + s * 0.30, cy + s * 0.5), (cx + s * 0.30, cy - s * 0.02),
                       (cx + s * 0.52, cy - s * 0.16), (cx + s * 0.30, cy - s * 0.44)], fill=c)
        elif kind == "settings":
            self.ellipse(cx - s * 0.44, cy - s * 0.44, s * 0.88, s * 0.88, None, outline=c, width=width)
            self.ellipse(cx - s * 0.16, cy - s * 0.16, s * 0.32, s * 0.32, c)
            for ang in (0, 90, 45, 135):
                pass
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                self.rect(cx + dx * s * 0.44 - (s * 0.11 if dx == 0 else 0),
                          cy + dy * s * 0.44 - (s * 0.11 if dy == 0 else 0),
                          s * 0.22 if dx == 0 else s * 0.16,
                          s * 0.22 if dy == 0 else s * 0.16, c, radius=2)
        elif kind == "play":
            self.poly([(cx - s * 0.26, cy - s * 0.42), (cx + s * 0.46, cy),
                       (cx - s * 0.26, cy + s * 0.42)], fill=c)
        elif kind == "search":
            self.ellipse(cx - s * 0.48, cy - s * 0.52, s * 0.68, s * 0.68, None, outline=c, width=width)
            self.d.line([(self.s(cx + s * 0.12), self.s(cy + s * 0.14)),
                         (self.s(cx + s * 0.5), self.s(cy + s * 0.52))], fill=c, width=max(2, self.s(width)))
        elif kind == "plus":
            self.rect(cx - s * 0.11, cy - s * 0.46, s * 0.22, s * 0.92, c, radius=2)
            self.rect(cx - s * 0.46, cy - s * 0.11, s * 0.92, s * 0.22, c, radius=2)

    def glyph_id(self, name):
        return {"HOME": "home", "PROFILES": "profiles", "MODS": "mods", "SERVERS": "servers",
                "CONTROLS": "controls", "SKINS": "skins", "SETTINGS": "settings"}.get(name, "home")


# --------------------------------------------------------------------------- content blocks
def server_panel(sc, x, y, w, h, accent=CYAN, radius=24, compact=False):
    sc.liquid(x, y, w, h, radius=radius, tint=34, scrim=78, accent=accent)
    sc.stext(x + 18, y + (11 if compact else 13), "LUCIFERMC", 12.5, WHITE, True, 1.2)
    # OFFICIAL pill, right aligned
    lab = "OFFICIAL"
    tw = sc.width_of(lab, 7.2, True, 1.1)
    pw = tw + 20
    sc.pill(x + w - 18 - pw, y + (11 if compact else 13), pw, 19,
            fill=lerp(MAGENTA, WHITE, 0.25), alpha=95, edge=rgba(WHITE, 190))
    sc.text_mid(x + w - 18 - pw / 2, y + (16 if compact else 18), lab, 7.2, WHITE, True, 1.1)
    sc.stext(x + 18, y + (31 if compact else 34), "LIFESTEEL SMP", 8.8, TEXT_3, True, 1.6)
    if h >= 108:
        py = y + h - 62
        sc.text(x + 18, py, "PLAYERS", 7.0, TEXT_3, True, 1.4)
        sc.text_end(x + w - 18, py, "12 / 200", 8.6, WHITE, True, 0.4)
        sc.rect(x + 18, py + 15, w - 36, 5, rgba(WHITE, 52), radius=3)
        sc.grad_rect(x + 18, py + 15, (w - 36) * 0.06 if w > 400 else (w - 36) * 0.32, 5,
                     lerp(accent, WHITE, 0.4), accent, radius=3)
    row = y + h - (28 if compact else 30)
    if w >= 360:
        sc.stext(x + 18, row, "play.lucifermc.fun", 9.6, accent, False, 0.2)
    live = "LIVE · 24ms"
    lw = sc.width_of(live, 8.6, True, 0.5)
    sc.dot(x + w - 18 - lw - 12, row + 6, 3.2, OK_GREEN)
    sc.send(x + w - 18, row, live, 8.6, OK_GREEN, True, 0.5)


def hero_panel(sc, x, y, w, h, accent=CYAN, radius=30, skin=True, launch=True, compact=False):
    """Instance hero: stats on top, spec rows on the left, the skin preview on the right.

    Type and sprite scale with the panel width, so a full-width hero does not end up as a
    small card lost in a big empty pane.
    """
    k = max(1.0, min(1.32, w / 720.0))
    sc.liquid(x, y, w, h, radius=radius, tint=32, scrim=72, accent=accent, magnify=0.06)
    base_size = 20 if not compact else 17
    sc.stext(x + 24, y + 18, "FABRIC 1.21.4", 7.8 * min(k, 1.2), accent, True, 1.4)
    sc.stext(x + 24, y + 31, "Shadow PvP", base_size * min(k, 1.25), WHITE, True, 0.2)

    stat_y = y + (68 if not compact else 62)
    span = w * (0.42 if not compact else 0.36)
    for i, (lab, val) in enumerate((("VERSION", "1.21.10"), ("FABRIC", "0.16.9"), ("ACTIVE", "42"))):
        sc.stat_block(x + 24 + i * (span / 3), stat_y, lab, val, accent=WHITE,
                      size=(15 if not compact else 12.5) * min(k, 1.25))

    rows = (("RENDERER", "MobileGlues"), ("SHADERS", "Complementary"),
            ("SERVER", "LuciferMC · 24ms"), ("MODS DIR", "6.0 GB free"))
    ry = stat_y + (46 if not compact else 34)
    for i, (lab, val) in enumerate(rows if not compact else rows[:3]):
        yy = ry + i * 24
        sc.text(x + 24, yy, lab, 7.2, TEXT_3, True, 1.4)
        sc.stext(x + 104, yy - 1.5, val, 9.4, WHITE, True, 0.2)

    if skin:
        cx = x + w * (0.72 if w < 900 else 0.78)
        sprite = base.skin_sprite(scale=13)
        avail = (y + h - 54) - (stat_y + 34)
        th = max(90, min(avail * 0.94, 330 * k, w * (0.34 if w >= 900 else 0.62)))
        tw = th * sprite.width / sprite.height
        sc.halo(cx, y + h - 54 - th * 0.45, tw * 0.62, accent, 42)
        img = sprite.resize((int(tw * S), int(th * S)), Image.LANCZOS)
        sc.img.alpha_composite(img, (sc.s(cx - tw / 2), sc.s(y + h - 52 - th)))
        sc.redraw()
        if w >= 900:
            # wide heroes get the instance badge floating under the preview
            bw2 = 150
            sc.pill(cx - bw2 / 2, y + h - 46, bw2, 24, fill=WHITE, alpha=54,
                    edge=rgba(WHITE, 160))
            sc.text_mid(cx, y + h - 39, "IMAGE · 1.21.10", 7.4, TEXT_2, True, 0.8)

    by = y + h - 44
    sc.stext(x + 24, by + 2, "6.0 GB", 15, WHITE, True, 0.3)
    gw = sc.width_of("6.0 GB", 15, True, 0.3)
    sc.stext(x + 24 + gw + 10, by + 7, "RAM ALLOC", 7.2, TEXT_3, True, 1.2)
    if launch:
        bw = 186
        sc.grad_rect(x + w - 24 - bw, by - 5, bw, 36, lerp(accent, WHITE, 0.5), accent, radius=18)
        sc.glyph("play", x + w - 24 - bw + 24, by + 13, 9, INK, 1.4)
        sc.text(x + w - 24 - bw + 42, by + 6, "READY TO LAUNCH", 8.4, INK, True, 0.9)


def instance_tile(sc, x, y, w, h, title, sub, active=False, accent=CYAN, radius=18, art="1.21.10"):
    sc.liquid(x, y, w, h, radius=radius, tint=30 if active else 26,
              scrim=60, accent=accent if active else CYAN)
    if active:
        sc.rect(x, y, w, h, None, radius=radius, outline=rgba(accent, 230), width=2.0)
    # little isometric block: the instance thumbnail
    ix, iy, sz = x + 12, y + 12, h - 24
    sc.rect(ix, iy, sz, sz, rgba(lerp(accent, WHITE, 0.55), 105), radius=9,
            outline=rgba(WHITE, 160), width=1.1)
    k = sz * 0.30
    sc.poly([(ix + sz / 2, iy + sz / 2 - k * 0.78), (ix + sz / 2 + k * 0.9, iy + sz / 2 - k * 0.2),
             (ix + sz / 2, iy + sz / 2 + k * 0.42), (ix + sz / 2 - k * 0.9, iy + sz / 2 - k * 0.2)],
            fill=rgba(WHITE, 150), outline=rgba(WHITE, 210), width=1)
    sc.poly([(ix + sz / 2, iy + sz / 2 + k * 0.42), (ix + sz / 2 + k * 0.9, iy + sz / 2 - k * 0.2),
             (ix + sz / 2 + k * 0.9, iy + sz / 2 + k * 0.30), (ix + sz / 2, iy + sz / 2 + k * 0.9)],
            fill=rgba(lerp(accent, (0, 0, 0), 0.25), 150))
    tx = x + h - 4
    sc.stext(tx, y + h * 0.22, title, 11, WHITE, True, 0.5)
    sc.stext(tx, y + h * 0.58, sub, 8.4, TEXT_3, True, 0.9)
    # version chip, top right
    lab = "1.21.10" if art == "1.21.10" else art
    tw = sc.width_of(lab, 7.4, True, 0.5)
    sc.pill(x + w - 16 - tw - 22, y + 13, tw + 20, 20,
            fill=WHITE, alpha=54, edge=rgba(WHITE, 150))
    sc.text_mid(x + w - 16 - tw / 2 - 11, y + 19, lab, 7.4, TEXT_2, True, 0.5)
    if active:
        sc.dot(x + w - 24 - tw - 28, y + 23, 3.4, accent)


def mods_strip(sc, x, y, w, accent=CYAN, h=38, label=True):
    sc.liquid(x, y, w, h, radius=h / 2, tint=26, scrim=52, accent=accent, spec=0.6)
    cx = x + 16
    if label:
        sc.stext(cx, y + h / 2 - 5, "TOP MODS", 7.4, TEXT_3, True, 1.2)
        cx += 78
    for m in MODS:
        tw = sc.width_of(m, 8.4, True, 0.5)
        sc.pill(cx, y + h / 2 - 11, tw + 18, 22, fill=WHITE, alpha=54, edge=WHITE, edge_alpha=120)
        sc.text(cx + 9, y + h / 2 - 6, m, 8.4, WHITE, True, 0.5)
        cx += tw + 26


def dock_bar(sc, x, y, w, h, active="HOME", accent=CYAN, labels=True, radius=None):
    radius = h / 2 if radius is None else radius
    sc.liquid(x, y, w, h, radius=radius, tint=40, scrim=58, accent=accent, magnify=0.03,
              shadow=110, spec=1.2)
    n = len(DOCK)
    step = w / n
    for i, name in enumerate(DOCK):
        cx = x + step * (i + 0.5)
        on = name == active
        if on:
            pw = 96 if labels else 56
            bar_y = y + h - 9
            sc.halo(cx, bar_y - 16, 34, accent, 60, blur=sc.s(16))
            sc.grad_rect(cx - pw / 2, bar_y - 6, pw, 4, lerp(accent, WHITE, 0.5), accent, radius=2)
        col = WHITE if on else TEXT_3
        icon_y = y + (h * 0.36 if labels else h * 0.5)
        sc.glyph(sc.glyph_id(name), cx, icon_y, 15 if labels else 17, col)
        if labels:
            sc.smid(cx, y + h * 0.60, name, 7.2,
                    WHITE if on else TEXT_3, True, 0.9)


def status_pills(sc, x, y):
    sc.stext(x, y, "9:41", 10, WHITE, True, 0.4)
    for i, kind in enumerate(("servers", "controls", "settings")):
        sc.glyph(kind, x + 760 + i * 30, y + 5, 11, TEXT_2)


# --------------------------------------------------------------------------- layouts
def l01(sc):
    """Floating crystal: top pill, hero left, server + instances right, dock bottom."""
    sc.liquid(PAD, PAD, 470, 54, radius=27, tint=42, scrim=30)
    sc.avatar(PAD + 27, PAD + 27, 17)
    sc.stext(PAD + 52, PAD + 13, "SAIFKHAN", 11.5, WHITE, True, 1.0)
    sc.stext(PAD + 52, PAD + 29, "LUCIFER LAUNCHER · PREMIUM", 7.2, TEXT_3, True, 1.1)
    bw = 150
    sc.liquid(W - PAD - bw, PAD, bw, 54, radius=27, tint=40, scrim=26)
    sc.glyph("search", W - PAD - bw + 24, PAD + 27, 12, TEXT_2)
    sc.text(W - PAD - bw + 42, PAD + 20, "SEARCH", 8.6, TEXT_3, True, 1.2)

    hero_panel(sc, PAD, 96, 700, 452, radius=34)
    server_panel(sc, PAD, 566, 700, 118)
    mods_strip(sc, PAD, 700, 700)

    rx, rw = 750, W - 750 - PAD
    sc.liquid(rx, 96, rw, 44, radius=22, tint=40, scrim=26)
    sc.stext(rx + 16, 108, "MY INSTANCES", 8.4, TEXT_3, True, 1.4)
    sc.send(rx + rw - 16, 108, "4 / 12", 8.4, CYAN, True, 0.8)
    items = (("Fabric 1.21.10", "SHADOW PVP · READY", True),
             ("LuciferMC SMP", "LIFESTEEL · ONLINE", False),
             ("CS Client", "PVP · 1.8.9", False))
    for i, (t, s, a) in enumerate(items):
        instance_tile(sc, rx, 152 + i * 92, rw, 80, t, s, active=a)
    sc.liquid(rx, 428, rw, 72, radius=20, tint=26, scrim=50)
    sc.glyph("plus", rx + 34, 464, 14, CYAN)
    sc.stext(rx + 58, 454, "+ NEW INSTANCE", 9.4, WHITE, True, 1.1)
    sc.stext(rx + 58, 468, "vanilla · modded · snapshots", 7.6, TEXT_3, True, 0.6)

    sc.liquid(rx, 512, rw, 172, radius=26, tint=30, scrim=70)
    sc.stext(rx + 18, 526, "SHADOW DRAGON ARSENAL", 8.4, MAGENTA, True, 1.2)
    sc.stext(rx + 18, 542, "MOD STORE", 13, WHITE, True, 0.8)
    sc.text(rx + 18, 566, "Sodium · Iris · new packs every week", 8.4, TEXT_3, False)
    sc.pill(rx + 18, 590, 120, 26, fill=MAGENTA, alpha=70, edge=rgba(MAGENTA, 200))
    sc.text(rx + 40, 597, "BROWSE", 8, WHITE, True, 1.0)
    sc.pill(rx + 148, 590, 120, 26)
    sc.text(rx + 166, 597, "HUD KEYS", 8, TEXT_2, True, 1.0)

    dock_bar(sc, PAD, H - PAD - 62, W - PAD * 2, 62)


def l02(sc):
    """Bottom sheet: wallpaper first, one big sheet holding everything."""
    sc.liquid(W / 2 - 210, PAD, 420, 44, radius=22, tint=40, scrim=24)
    sc.avatar(W / 2 - 186, PAD + 22, 14)
    sc.stext(W / 2 - 164, PAD + 15, "SAIFKHAN", 10, WHITE, True, 0.9)
    sc.stext(W / 2 - 164, PAD + 28, "SHADOW DRAGON", 7, TEXT_3, True, 1.0)
    sc.badge(W / 2 + 82, PAD + 12, "PREMIUM", lerp(MAGENTA, WHITE, 0.25), 7.2)
    sc.smid(W / 2, 76, "READY WHEN YOU ARE", 7.4, TEXT_2, True, 2.2)

    sheet_y = 372
    sc.liquid(PAD, sheet_y, W - PAD * 2, H - sheet_y - PAD, radius=42, tint=38, scrim=76,
              magnify=0.03, shadow=120)
    sc.rect(W / 2 - 34, sheet_y + 14, 68, 4, rgba(WHITE, 190), radius=2)

    # server row inside the sheet
    sc.stext(PAD + 30, sheet_y + 34, "LUCIFERMC", 12, WHITE, True, 1.2)
    sc.stext(PAD + 30, sheet_y + 50, "LIFESTEEL SMP · play.lucifermc.fun", 8.6, TEXT_3, True, 0.6)
    sc.dot(W - PAD - 150, sheet_y + 44, 3.4, OK_GREEN)
    sc.send(W - PAD - 30, sheet_y + 38, "LIVE · 24ms", 8.6, OK_GREEN, True, 0.6)

    cards_y = sheet_y + 76
    cw = (W - PAD * 2 - 60 - 2 * 18) / 3
    for i, (t, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP", True),
                                    ("LuciferMC SMP", "LIFESTEEL", False),
                                    ("CS Client", "1.8.9 PVP", False))):
        instance_tile(sc, PAD + 30 + i * (cw + 18), cards_y, cw, 80, t, s2, active=a, radius=20)

    # hero row
    hx, hy = PAD + 30, cards_y + 96
    hw = (W - PAD * 2 - 60) * 0.56
    sc.liquid(hx, hy, hw, 244, radius=26, tint=30, scrim=70)
    sc.stext(hx + 20, hy + 16, "FABRIC 1.21.4", 7.6, CYAN, True, 1.3)  # hero header
    sc.stext(hx + 20, hy + 28, "Shadow PvP", 18, WHITE, True, 0.2)
    for i, (lab, val) in enumerate((("VERSION", "1.21.10"), ("FABRIC", "0.16.9"), ("ACTIVE", "42"))):
        sc.stat_block(hx + 20 + i * 92, hy + 58, lab, val, accent=WHITE)
    sprite = base.skin_sprite(scale=11)
    th = 150
    tw = th * sprite.width / sprite.height
    sc.img.alpha_composite(sprite.resize((int(tw * S), int(th * S)), Image.LANCZOS),
                           (sc.s(hx + hw * 0.66), sc.s(hy + 40)))
    sc.redraw()
    sc.halo(hx + hw * 0.72, hy + 120, 76, CYAN, 34)
    sc.grad_rect(hx + 20, hy + 176, hw - 40, 34, lerp(CYAN, WHITE, 0.5), CYAN, radius=17)
    sc.glyph("play", hx + 42, hy + 193, 9, INK, 1.4)
    sc.text(hx + 62, hy + 186, "READY TO LAUNCH", 9, INK, True, 0.9)

    # right stack: ram + mods
    rx = hx + hw + 18
    rw = W - PAD - 30 - rx
    sc.liquid(rx, hy, rw, 92, radius=24, tint=30, scrim=66)
    sc.stext(rx + 18, hy + 14, "RAM", 7.4, TEXT_3, True, 1.3)
    sc.stext(rx + 18, hy + 26, "6.0 GB", 17, WHITE, True, 0.3)
    sc.rect(rx + 18, hy + 54, rw - 36, 6, rgba(WHITE, 60), radius=3)
    sc.grad_rect(rx + 18, hy + 54, (rw - 36) * 0.62, 6, lerp(CYAN, WHITE, 0.4), CYAN, radius=3)
    sc.liquid(rx, hy + 104, rw, 140, radius=24, tint=30, scrim=66)
    sc.stext(rx + 18, hy + 118, "SHADERS", 7.4, TEXT_3, True, 1.3)
    sc.stext(rx + 18, hy + 130, "Complementary", 13, WHITE, True, 0.3)
    sc.stext(rx + 18, hy + 150, "Ultra · 42 fps target", 8, TEXT_3, False)
    sc.rect(rx + 18, hy + 172, rw - 36, 1.2, rgba(WHITE, 46), radius=1)
    sc.stext(rx + 18, hy + 182, "MODS DIR", 7.2, TEXT_3, True, 1.3)
    sc.stext(rx + 18, hy + 194, "12.4 GB · 42 mods", 10, WHITE, True, 0.2)

    mods_strip(sc, hx, hy + 260, hw, h=40)
    dock_bar(sc, PAD + 30, H - PAD - 22 - 58, W - PAD * 2 - 60, 58)


def l03(sc):
    """Side rail: vertical glass rail on the left, big hero on the right."""
    rail_w = 108
    sc.liquid(PAD, PAD, rail_w, H - PAD * 2, radius=40, tint=40, scrim=64, magnify=0.02)
    sc.avatar(PAD + rail_w / 2, PAD + 44, 18)
    sc.smid(PAD + rail_w / 2, PAD + 74, "SAIF", 8, WHITE, True, 1.0)
    top = 108
    for i, name in enumerate(DOCK):
        cy = top + i * 92
        on = i == 0
        if on:
            sc.rect(PAD + 14, cy - 26, rail_w - 28, 74, rgba(WHITE, 52), radius=22,
                    outline=rgba(WHITE, 170), width=1.2)
            sc.rect(PAD + 8, cy + 6, 3.4, 30, rgba(CYAN, 255), radius=2)
        sc.glyph(sc.glyph_id(name), PAD + rail_w / 2, cy, 16, WHITE if on else TEXT_3)
        sc.smid(PAD + rail_w / 2, cy + 26, name[:7], 6.8, WHITE if on else TEXT_3, True, 0.8)

    x0 = PAD + rail_w + 18
    w0 = W - x0 - PAD
    # top: title + search
    sc.stext(x0, 30, "HOME", 22, WHITE, True, 1.6)
    sc.stext(x0, 58, "SAIFKHAN · SHADOW DRAGON · PREMIUM", 8.2, TEXT_3, True, 1.2)
    sc.liquid(W - PAD - 190, PAD, 190, 48, radius=24, tint=38, scrim=28)
    sc.glyph("search", W - PAD - 166, PAD + 24, 12, TEXT_2)
    sc.text(W - PAD - 146, PAD + 17, "SEARCH", 8.4, TEXT_3, True, 1.2)

    hw = w0 * 0.60
    hero_panel(sc, x0, 96, hw, 424, radius=32)
    sx = x0 + hw + 16
    sw = w0 - hw - 16
    server_panel(sc, sx, 96, sw, 158, radius=26)
    sc.liquid(sx, 270, sw, 250, radius=26, tint=30, scrim=70)
    sc.stext(sx + 18, 282, "MODS", 8.2, TEXT_3, True, 1.4)
    sc.send(sx + sw - 18, 282, "42 ACTIVE", 8.2, OK_GREEN, True, 0.6)
    for i, m in enumerate(MODS):
        yy = 310 + i * 36
        sc.rect(sx + 18, yy - 4, sw - 36, 1.2, rgba(WHITE, 46), radius=1)
        sc.dot(sx + 26, yy + 12, 3.0, CYAN)
        sc.text(sx + 40, yy + 5, m, 9.6, WHITE, True, 0.4)
        sc.text_end(sx + sw - 18 - 34, yy + 5, "v" + str(2 + i) + "." + str(i + 3), 8, TEXT_3, False)
        sc.pill(sx + sw - 46, yy + 2, 28, 16, fill=OK_GREEN, alpha=60, edge=rgba(OK_GREEN, 160))

    by = 540
    mods_strip(sc, x0, by, w0, h=42)
    cw = (w0 - 18) / 2
    for i, (t2, s2) in enumerate((("LuciferMC SMP", "LIFESTEEL · ONLINE"), ("CS Client", "PVP · 1.8.9"))):
        instance_tile(sc, x0 + i * (cw + 18), by + 58, cw, 96, t2, s2, active=False)
    qy = H - PAD - 96
    sc.liquid(x0, qy, w0, 96, radius=28, tint=32, scrim=66)
    sc.stext(x0 + 20, qy + 18, "QUICK LAUNCH", 8.2, TEXT_3, True, 1.4)
    sc.stext(x0 + 20, qy + 34, "Shadow PvP · Fabric 1.21.4", 13, WHITE, True, 0.4)
    sc.stext(x0 + 20, qy + 58, "1.21.10 · 42 mods · Complementary", 8.2, TEXT_3, False, 0.4)
    sc.grad_rect(x0 + w0 - 210, qy + 32, 190, 38, lerp(CYAN, WHITE, 0.5), CYAN, radius=19)
    sc.glyph("play", x0 + w0 - 186, qy + 51, 10, INK, 1.4)
    sc.text(x0 + w0 - 164, qy + 43, "LAUNCH GAME", 9.2, INK, True, 1.0)


def l04(sc):
    """Split glass: two columns, dock floating across the bottom."""
    sc.liquid(PAD, PAD, W - PAD * 2, 60, radius=30, tint=42, scrim=30)
    sc.avatar(PAD + 30, PAD + 30, 18)
    sc.stext(PAD + 56, PAD + 15, "SAIFKHAN", 12, WHITE, True, 1.0)
    sc.stext(PAD + 56, PAD + 33, "SHADOW DRAGON ARSENAL", 7.2, TEXT_3, True, 1.2)
    sc.badge(W / 2 - 30, PAD + 21, "PREMIUM", lerp(MAGENTA, WHITE, 0.25), 7.2)
    sc.stext(W - PAD - 250, PAD + 16, "LUCIFERMC", 10, WHITE, True, 1.0)
    sc.stext(W - PAD - 250, PAD + 34, "play.lucifermc.fun · 24ms", 8, OK_GREEN, False, 0.3)
    sc.dot(W - PAD - 30, PAD + 30, 3.6, OK_GREEN)

    col_w = (W - PAD * 2 - 20) / 2
    lx, rx = PAD, PAD + col_w + 20
    sc.liquid(lx, 96, col_w, 46, radius=23, tint=36, scrim=26)
    sc.stext(lx + 16, 108, "INSTANCES", 8.4, TEXT_3, True, 1.5)
    sc.send(lx + col_w - 16, 108, "3 OF 12", 8.4, CYAN, True, 0.8)
    for i, (t, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP · READY", True),
                                    ("LuciferMC SMP", "LIFESTEEL · ONLINE", False),
                                    ("CS Client", "PVP · 1.8.9", False))):
        instance_tile(sc, lx, 154 + i * 92, col_w, 80, t, s2, active=a)
    sc.liquid(lx, 430, col_w, 68, radius=22, tint=26, scrim=52)
    sc.glyph("plus", lx + 32, 464, 13, CYAN)
    sc.stext(lx + 54, 452, "+ NEW INSTANCE", 9.4, WHITE, True, 1.1)
    sc.stext(lx + 54, 466, "vanilla · modded · snapshots", 7.4, TEXT_3, True, 0.6)
    mods_strip(sc, lx, 514, col_w, h=38)
    sc.liquid(lx, 566, col_w, 118, radius=24, tint=28, scrim=70)
    sc.stext(lx + 18, 580, "MOD STORE", 8.2, MAGENTA, True, 1.3)
    sc.stext(lx + 18, 594, "Shadow Dragon Arsenal", 12.5, WHITE, True, 0.4)
    sc.text(lx + 18, 616, "Sodium · Iris · new packs weekly", 8.2, TEXT_3, False)
    sc.pill(lx + 18, 640, 112, 26, fill=MAGENTA, alpha=74, edge=rgba(MAGENTA, 200))
    sc.text(lx + 36, 647, "BROWSE", 8, WHITE, True, 1.0)
    sc.pill(lx + 140, 640, 112, 26)
    sc.text(lx + 158, 647, "HUD KEYS", 8, TEXT_2, True, 1.0)

    hero_panel(sc, rx, 96, col_w, 300, radius=32, compact=True)
    server_panel(sc, rx, 412, col_w, 120, radius=26)
    sc.liquid(rx, 548, col_w, 136, radius=26, tint=30, scrim=68)
    sc.stext(rx + 18, 562, "SETTINGS SNAPSHOT", 8.2, TEXT_3, True, 1.4)
    for i, (lab, val) in enumerate((("RENDER DISTANCE", "12 chunks"), ("SIM DISTANCE", "8 chunks"),
                                    ("GRAPHICS", "Fancy · Complementary"))):
        yy = 584 + i * 26
        sc.text(rx + 18, yy, lab, 8.4, TEXT_3, True, 0.9)
        sc.text_end(rx + col_w - 18, yy, val, 8.8, WHITE, True, 0.4)
    dock_bar(sc, PAD, H - PAD - 62, W - PAD * 2, 62)


def l05(sc):
    """Island hop: no big panels, floating glass islands over the wallpaper."""
    sc.smid(W / 2, 26, "LUCIFER LAUNCHER", 9, TEXT_2, True, 3.2)

    sc.liquid(PAD, 52, 320, 66, radius=33, tint=40, scrim=40)
    sc.avatar(PAD + 33, 85, 20)
    sc.stext(PAD + 62, 66, "SAIFKHAN", 11, WHITE, True, 1.0)
    sc.stext(PAD + 62, 84, "SHADOW DRAGON · PREMIUM", 7.2, TEXT_3, True, 1.1)

    sc.liquid(W - PAD - 340, 52, 340, 66, radius=33, tint=40, scrim=46)
    sc.stext(W - PAD - 322, 66, "LUCIFERMC", 11, WHITE, True, 1.0)
    sc.stext(W - PAD - 322, 84, "LIFESTEEL SMP · 24ms", 8, OK_GREEN, False, 0.4)
    sc.dot(W - PAD - 30, 85, 4.2, OK_GREEN)

    # left stat stack
    for i, (lab, val, col) in enumerate((("FPS", "60", CYAN), ("RAM", "6.0 GB", WHITE),
                                         ("MODS", "42", MAGENTA), ("SHADER", "Compl.", OK_GREEN))):
        sc.liquid(PAD, 140 + i * 92, 176, 78, radius=24, tint=32, scrim=64)
        sc.stext(PAD + 18, 154 + i * 92, lab, 7.4, TEXT_3, True, 1.4)
        sc.stext(PAD + 18, 168 + i * 92, val, 17, col, True, 0.3)

    # instances island (right)
    ix = W - PAD - 380
    sc.liquid(ix, 140, 380, 244, radius=30, tint=32, scrim=70)
    sc.stext(ix + 18, 154, "INSTANCES", 8.2, TEXT_3, True, 1.4)
    for i, (t, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP", True),
                                    ("LuciferMC SMP", "LIFESTEEL", False),
                                    ("CS Client", "1.8.9", False))):
        yy = 176 + i * 46
        sc.rect(ix + 14, yy, 352, 40, rgba(WHITE, 34 if not a else 64), radius=14,
                outline=rgba(a and rgba(CYAN, 210) or WHITE, 150 if a else 90), width=1.1)
        sc.dot(ix + 30, yy + 20, 3.0, CYAN if a else TEXT_3)
        sc.text(ix + 42, yy + 13, t, 9.4, WHITE, True, 0.5)
        sc.text_end(ix + 356, yy + 14, s2, 7.4, TEXT_3, True, 0.7)

    # centre launch island
    cx, cy = 800, 470
    sc.liquid(cx - 250, cy - 96, 500, 192, radius=42, tint=36, scrim=64, magnify=0.07)
    sc.stext(cx - 224, cy - 74, "FABRIC 1.21.4", 7.8, CYAN, True, 1.4)
    sc.stext(cx - 224, cy - 60, "Shadow PvP", 22, WHITE, True, 0.2)
    sc.stext(cx - 224, cy - 26, "1.21.10 · Fabric 0.16.9 · 42 mods active", 8.4, TEXT_3, True, 0.6)
    sc.grad_rect(cx - 224, cy + 6, 268, 46, lerp(CYAN, WHITE, 0.55), CYAN, radius=23)
    sc.glyph("play", cx - 196, cy + 29, 12, INK, 1.6)
    sc.text(cx - 172, cy + 17, "READY TO LAUNCH", 11, INK, True, 1.1)
    sc.pill(cx + 58, cy + 6, 166, 46, fill=WHITE, alpha=58, edge=WHITE, edge_alpha=170)
    sc.text(cx + 84, cy + 22, "EDIT PROFILE", 9, WHITE, True, 1.0)

    # recent worlds island (fills the lower-left gap)
    sc.liquid(PAD, 500, 400, 190, radius=28, tint=30, scrim=70)
    sc.stext(PAD + 18, 514, "RECENT WORLDS", 8.2, TEXT_3, True, 1.4)
    for i, (nm, sub) in enumerate((("Lifesteel Base", "creative · spawn"), ("Shadow Arena", "pvp · 1v1"),
                                   ("Dragon Vault", "survival · day 42"))):
        yy = 536 + i * 42
        sc.rect(PAD + 14, yy, 372, 36, rgba(WHITE, 40), radius=12,
                outline=rgba(WHITE, 96), width=1)
        sc.glyph("servers", PAD + 32, yy + 18, 8, CYAN)
        sc.text(PAD + 48, yy + 9, nm, 9, WHITE, True, 0.4)
        sc.text_end(PAD + 372, yy + 11, sub, 7.2, TEXT_3, False, 0.3)

    # floating mod chips row
    sc.liquid(PAD, 706, 720, 56, radius=28, tint=30, scrim=56)
    sc.stext(PAD + 18, 726, "TOP MODS", 7.2, TEXT_3, True, 1.3)
    x = PAD + 92
    for m in MODS:
        tw = sc.width_of(m, 8.2, True, 0.4)
        sc.pill(x, 654, tw + 16, 26, fill=WHITE, alpha=56, edge=WHITE, edge_alpha=130)
        sc.text(x + 8, 660, m, 8.2, WHITE, True, 0.4)
        x += tw + 24

    sc.liquid(W - PAD - 340, 706, 340, 56, radius=28, tint=30, scrim=56)
    sc.stext(W - PAD - 322, 726, "SERVER PING", 7.2, TEXT_3, True, 1.3)
    sc.text_end(W - PAD - 22, 720, "24 ms", 15, OK_GREEN, True, 0.4)

    # dock as three islands
    seg = (W - PAD * 2 - 40) / 3
    groups = (DOCK[:3], DOCK[3:5], DOCK[5:])
    for gi, group in enumerate(groups):
        gx = PAD + gi * (seg + 20)
        sc.liquid(gx, H - PAD - 66, seg, 66, radius=33, tint=40, scrim=56, magnify=0.03)
        for i, name in enumerate(group):
            cx2 = gx + seg * ((i + 0.5) / len(group))
            on = name == "HOME"
            sc.glyph(sc.glyph_id(name), cx2, H - PAD - 40, 16, WHITE if on else TEXT_3)
            sc.smid(cx2, H - PAD - 20, name, 7, WHITE if on else TEXT_3, True, 0.9)
            if on:
                sc.grad_rect(cx2 - 22, H - PAD - 9, 44, 3, lerp(CYAN, WHITE, 0.5), CYAN, radius=2)


def l06(sc):
    """Tile grid: header + 3x2 grid of equal glass tiles."""
    sc.liquid(PAD, PAD, W - PAD * 2, 62, radius=31, tint=42, scrim=30)
    sc.avatar(PAD + 31, PAD + 31, 18)
    sc.stext(PAD + 58, PAD + 16, "SAIFKHAN", 12, WHITE, True, 1.0)
    sc.stext(PAD + 58, PAD + 34, "SHADOW DRAGON · PREMIUM", 7.2, TEXT_3, True, 1.1)
    sc.stext(W - PAD - 300, PAD + 17, "SHADOW PVP", 10, WHITE, True, 0.9)
    sc.stext(W - PAD - 300, PAD + 35, "Fabric 1.21.4 · 1.21.10", 8, TEXT_3, False, 0.4)
    sc.pill(W - PAD - 176, PAD + 17, 152, 28, fill=OK_GREEN, alpha=78, edge=rgba(OK_GREEN, 190))
    sc.dot(W - PAD - 158, PAD + 31, 3.4, OK_GREEN)
    sc.text(W - PAD - 148, PAD + 24, "READY", 8.4, WHITE, True, 1.0)

    gw, gh = (W - PAD * 2 - 2 * 16) / 3, (H - 96 - PAD - 84 - 2 * 16) / 2
    gx0, gy0 = PAD, 96
    # big hero tile spans two rows in column 1
    hero_panel(sc, gx0, gy0, gw, gh * 2 + 16, radius=32, compact=True)

    server_panel(sc, gx0 + gw + 16, gy0, gw, 150, radius=28)
    sc.liquid(gx0 + gw + 16, gy0 + 166, gw, gh - 150, radius=28, tint=30, scrim=70)
    sc.stext(gx0 + gw + 34, gy0 + 180, "MODS", 8.2, TEXT_3, True, 1.4)
    sc.send(gx0 + gw * 2 + 16 - 18, gy0 + 180, "42 ACTIVE", 8.2, OK_GREEN, True, 0.8)
    for i, m in enumerate(MODS):
        yy = gy0 + 204 + i * 24
        sc.dot(gx0 + gw + 38, yy + 5, 2.6, CYAN)
        sc.text(gx0 + gw + 50, yy - 2, m, 9, WHITE, True, 0.5)
        sc.text_end(gx0 + gw * 2 + 16 - 18, yy - 1, "on", 7.4, TEXT_3, True, 0.6)

    x3 = gx0 + (gw + 16) * 2
    sc.liquid(x3, gy0, gw, gh, radius=28, tint=30, scrim=70)
    sc.stext(x3 + 18, gy0 + 14, "TOP MODS", 8.2, TEXT_3, True, 1.4)
    for i, m in enumerate(MODS):
        yy = gy0 + 38 + i * 24
        sc.dot(x3 + 26, yy + 5, 2.8, CYAN)
        sc.text(x3 + 38, yy - 2, m, 9.2, WHITE, True, 0.5)
    sc.liquid(x3, gy0 + gh + 16, gw, gh, radius=28, tint=30, scrim=70)
    sc.stext(x3 + 18, gy0 + gh + 30, "SERVERS", 8.2, TEXT_3, True, 1.4)
    sc.stext(x3 + 18, gy0 + gh + 46, "LUCIFERMC", 13, WHITE, True, 0.6)
    sc.stext(x3 + 18, gy0 + gh + 64, "LIFESTEEL · 24ms", 8.4, OK_GREEN, False, 0.4)
    sc.stext(x3 + 18, gy0 + gh + 82, "play.lucifermc.fun", 8.4, CYAN, False, 0.3)

    cx2 = gx0 + gw + 16
    sc.liquid(cx2, gy0 + gh + 16, gw, gh, radius=28, tint=30, scrim=70)
    sc.stext(cx2 + 18, gy0 + gh + 30, "INSTANCES", 8.2, TEXT_3, True, 1.4)
    for i, (t2, sub2) in enumerate((("Fabric 1.21.10", "READY"), ("LuciferMC SMP", "ONLINE"),
                                    ("CS Client", "1.8.9"), ("+ New Instance", "VANILLA"))):
        yy = gy0 + gh + 48 + i * 56
        sc.rect(cx2 + 16, yy, gw - 32, 48, rgba(WHITE, 42 if i < 3 else 26), radius=14,
                outline=rgba(WHITE if i else CYAN, 110 if i else 200), width=1.0)
        sc.glyph("plus" if i == 3 else "servers", cx2 + 38, yy + 24, 8,
                 CYAN if i in (0, 3) else TEXT_3)
        sc.text(cx2 + 54, yy + 12, t2, 9, WHITE, True, 0.5)
        sc.text(cx2 + 54, yy + 29, sub2, 7.2, TEXT_3, True, 0.8)
    dock_bar(sc, PAD, H - PAD - 62, W - PAD * 2, 62)


def l07(sc):
    """iOS settings list: one full-height sheet, grouped rows, preview on the right."""
    sc.liquid(PAD, PAD, 940, H - PAD * 2, radius=42, tint=40, scrim=76, magnify=0.02)
    sc.stext(PAD + 30, PAD + 22, "SETTINGS", 20, WHITE, True, 1.8)
    sc.stext(PAD + 30, PAD + 52, "SAIFKHAN · SHADOW DRAGON", 8.2, TEXT_3, True, 1.2)
    sc.liquid(W - PAD - 260, PAD + 18, 260, 44, radius=22, tint=40, scrim=24)
    sc.glyph("search", W - PAD - 236, PAD + 40, 11, TEXT_2)
    sc.text(W - PAD - 218, PAD + 34, "SEARCH SETTINGS", 7.6, TEXT_3, True, 1.1)

    y = PAD + 84
    groups = (
        ("GAME", (("Renderer", "MobileGlues", True), ("FPS overlay", "ON · draggable", True),
                  ("1.21+ FPS Pack", "ON", True))),
        ("DISPLAY", (("Resolution scale", "100 %", False), ("Sustained performance", "OFF", False),
                     ("Ignore notch", "ON", False))),
        ("PERFORMANCE", (("1.21+ FPS Pack", "ON", True), ("Surface mode", "Zero-copy", True),
                         ("Vsync", "Off", False), ("Frame limiter", "Unlimited", False))),
        ("ACCOUNT", (("Profile", "SAIFKHAN", False), ("Skin", "Shadow Dragon", False),
                     ("Mods folder", "12.4 GB used", False))),
    )
    for gname, rows in groups:
        sc.stext(PAD + 30, y, gname, 7.6, TEXT_3, True, 1.8)
        y += 18
        rh = 46
        sc.rect(PAD + 22, y, 896, rh * len(rows) + 10, rgba(WHITE, 26), radius=20,
                outline=rgba(WHITE, 96), width=1.1)
        for i, (lab, val, accent_row) in enumerate(rows):
            yy = y + 6 + i * rh
            if i:
                sc.rect(PAD + 58, yy - 1, 860, 1, rgba(WHITE, 40), radius=1)
            sc.text(PAD + 30, yy + 15, lab, 9.8, WHITE, True, 0.4)
            if accent_row:
                sc.dot(PAD + 46, yy + 22, 3.2, CYAN)
            sc.text_end(PAD + 22 + 866, yy + 15, val, 9.2, TEXT_2, False, 0.3)
            sc.text_end(PAD + 22 + 882, yy + 14, "›", 12, TEXT_3, True, 0)
        y += rh * len(rows) + 24

    # right column preview
    rx = PAD + 940 + 20
    rw = W - rx - PAD
    hero_panel(sc, rx, PAD, rw, 300, radius=32, compact=True, skin=True)
    server_panel(sc, rx, PAD + 316, rw, 124, radius=28)
    sc.liquid(rx, PAD + 456, rw, 236, radius=30, tint=30, scrim=72)
    sc.stext(rx + 20, PAD + 472, "INSTANCES", 8.2, TEXT_3, True, 1.4)
    for i, (t, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP", True),
                                    ("LuciferMC SMP", "LIFESTEEL", False),
                                    ("CS Client", "1.8.9", False))):
        yy = PAD + 494 + i * 62
        sc.rect(rx + 16, yy, rw - 32, 54, rgba(WHITE, 40 if not a else 66), radius=16,
                outline=rgba(CYAN if a else WHITE, 190 if a else 96), width=1.1)
        sc.text(rx + 32, yy + 12, t, 9.6, WHITE, True, 0.5)
        sc.text(rx + 32, yy + 30, s2, 7.6, TEXT_3, True, 0.8)
        sc.glyph("play", rx + rw - 40, yy + 27, 9, CYAN if a else TEXT_3)


def l08(sc):
    """Orbit: circular launch core with the seven sections orbiting it."""
    sc.liquid(PAD, PAD, W - PAD * 2, 56, radius=28, tint=42, scrim=28)
    sc.avatar(PAD + 28, PAD + 28, 17)
    sc.stext(PAD + 53, PAD + 14, "SAIFKHAN", 11, WHITE, True, 1.0)
    sc.stext(PAD + 53, PAD + 31, "SHADOW DRAGON", 7, TEXT_3, True, 1.1)
    sc.smid(W / 2, PAD + 20, "LUCIFER LAUNCHER", 8.4, TEXT_2, True, 3.0)
    sc.badge(W - PAD - 150, PAD + 17, "PREMIUM", lerp(MAGENTA, WHITE, 0.25), 7.4)

    cx, cy = W / 2, 470
    # orbit ring
    ring = Image.new("RGBA", sc.img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([sc.s(cx - 300), sc.s(cy - 300), sc.s(cx + 300), sc.s(cy + 300)],
                                 outline=rgba(WHITE, 54), width=sc.s(1.4))
    ImageDraw.Draw(ring).ellipse([sc.s(cx - 210), sc.s(cy - 210), sc.s(cx + 210), sc.s(cy + 210)],
                                 outline=rgba(WHITE, 34), width=sc.s(1.2))
    sc.img.alpha_composite(ring.filter(ImageFilter.GaussianBlur(sc.s(0.6))))
    sc.redraw()

    # core
    sc.liquid(cx - 170, cy - 170, 340, 340, radius=170, tint=44, scrim=62, magnify=0.09)
    sc.smid(cx, cy - 108, "FABRIC 1.21.4", 8, CYAN, True, 1.6)
    sprite = base.skin_sprite(scale=9)
    th = 150
    tw = th * sprite.width / sprite.height
    sc.img.alpha_composite(sprite.resize((int(tw * S), int(th * S)), Image.LANCZOS),
                           (sc.s(cx - tw / 2), sc.s(cy - 92)))
    sc.redraw()
    sc.smid(cx, cy + 62, "Shadow PvP", 15, WHITE, True, 0.3)
    sc.smid(cx, cy + 82, "1.21.10 · 42 mods", 8, TEXT_3, True, 0.6)
    sc.ellipse(cx - 46, cy + 98, 92, 92, fill=rgba(lerp(CYAN, WHITE, 0.45), 240),
               outline=rgba(WHITE, 235), width=1.4)
    sc.glyph("play", cx + 4, cy + 144, 15, INK, 2)

    # orbit chips
    import math
    r = 300
    for i, name in enumerate(DOCK):
        ang = -math.pi / 2 + i * (2 * math.pi / len(DOCK))
        px, py = cx + math.cos(ang) * r * 1.02, cy + math.sin(ang) * r * 0.78
        bw, bh = 132, 54
        sc.liquid(px - bw / 2, py - bh / 2, bw, bh, radius=27, tint=38, scrim=46, magnify=0.04)
        on = name == "HOME"
        sc.glyph(sc.glyph_id(name), px - 38, py, 13, WHITE if on else TEXT_3)
        sc.text(px - 22, py - 5, name, 7.6, WHITE if on else TEXT_2, True, 0.9)
        if on:
            sc.dot(px + 46, py - 12, 3.0, CYAN)

    sc.liquid(W / 2 - 300, H - PAD - 74, 600, 62, radius=31, tint=40, scrim=54)
    sc.stext(W / 2 - 278, H - PAD - 54, "SERVER", 7.4, TEXT_3, True, 1.4)
    sc.text(W / 2 - 222, H - PAD - 56, "LUCIFERMC · LIFESTEEL SMP", 9.6, WHITE, True, 0.6)
    sc.dot(W / 2 + 94, H - PAD - 40, 3.2, OK_GREEN)
    sc.text(W / 2 + 104, H - PAD - 47, "LIVE · 24ms", 8.6, OK_GREEN, True, 0.5)
    sc.send(W / 2 + 278, H - PAD - 56, "play.lucifermc.fun", 8.2, CYAN, False, 0.2)


def l09(sc):
    """Tab bar: wide hero, quick cards, instance rail, iOS tab bar at the bottom."""
    sc.liquid(PAD, PAD, 520, 52, radius=26, tint=42, scrim=28)
    sc.avatar(PAD + 26, PAD + 26, 16)
    sc.stext(PAD + 50, PAD + 12, "SAIFKHAN", 11, WHITE, True, 1.0)
    sc.stext(PAD + 50, PAD + 28, "PREMIUM · SHADOW DRAGON", 7, TEXT_3, True, 1.1)
    sc.liquid(W - PAD - 200, PAD, 200, 52, radius=26, tint=40, scrim=26)
    sc.glyph("search", W - PAD - 174, PAD + 26, 12, TEXT_2)
    sc.text(W - PAD - 154, PAD + 19, "SEARCH", 8.4, TEXT_3, True, 1.2)

    hero_panel(sc, PAD, 88, W - PAD * 2, 292, radius=36, compact=True)

    gy = 396
    cw = (W - PAD * 2 - 3 * 16) / 4
    cards = (("MODS", "42 active", CYAN), ("SHADERS", "Complementary", MAGENTA),
             ("RAM", "6.0 GB / 8", WHITE), ("SERVER", "LIVE · 24ms", OK_GREEN))
    for i, (lab, val, col) in enumerate(cards):
        x = PAD + i * (cw + 16)
        sc.liquid(x, gy, cw, 96, radius=26, tint=30, scrim=66)
        sc.stext(x + 16, gy + 14, lab, 7.4, TEXT_3, True, 1.4)
        sc.stext(x + 16, gy + 30, val, 12.5, col, True, 0.3)
        sc.rect(x + 16, gy + 62, cw - 32, 4, rgba(WHITE, 54), radius=2)
        sc.grad_rect(x + 16, gy + 62, (cw - 32) * (0.62 if i != 3 else 0.24), 4,
                     lerp(col, WHITE, 0.35), col, radius=2)

    mods_strip(sc, PAD, 508, W - PAD * 2, h=42, label=True)

    # instance rail
    ix = PAD
    iw = W - PAD * 2
    sc.liquid(ix, 566, iw, 46, radius=23, tint=36, scrim=26)
    sc.stext(ix + 16, 578, "LAST PLAYED", 8.2, TEXT_3, True, 1.5)
    sc.send(ix + iw - 16, 578, "3 INSTANCES", 8.2, CYAN, True, 0.8)
    tile_w = (iw - 2 * 16) / 3
    for i, (t2, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP · READY", True),
                                     ("LuciferMC SMP", "LIFESTEEL · ONLINE", False),
                                     ("CS Client", "PVP · 1.8.9", False))):
        instance_tile(sc, ix + i * (tile_w + 16), 624, tile_w, 82, t2, s2, active=a, radius=22)

    sc.liquid(ix, 716, iw, 62, radius=31, tint=30, scrim=54)
    sc.stext(ix + 18, 730, "SHADOW DRAGON ARSENAL", 7.2, MAGENTA, True, 1.3)
    sc.stext(ix + 18, 742, "MOD STORE", 11, WHITE, True, 0.8)
    sc.pill(ix + iw - 260, 733, 118, 28, fill=MAGENTA, alpha=80, edge=rgba(MAGENTA, 205))
    sc.text(ix + iw - 240, 740, "BROWSE", 8, WHITE, True, 1.0)
    sc.pill(ix + iw - 130, 733, 112, 28)
    sc.text(ix + iw - 112, 740, "HUD KEYS", 8, TEXT_2, True, 1.0)

    # tab bar
    ty = H - PAD - 74
    sc.liquid(PAD, ty, W - PAD * 2, 74, radius=37, tint=44, scrim=58, magnify=0.02, shadow=120)
    tabs = ("HOME", "PROFILES", "MODS", "SERVERS", "SETTINGS")
    step = (W - PAD * 2) / len(tabs)
    for i, name in enumerate(tabs):
        cx = PAD + step * (i + 0.5)
        on = i == 0
        if on:
            sc.rect(cx - 62, ty + 14, 124, 46, rgba(WHITE, 60), radius=23,
                    outline=rgba(WHITE, 180), width=1.2)
        sc.glyph(sc.glyph_id(name), cx, ty + 30, 14, WHITE if on else TEXT_3)
        sc.smid(cx, ty + 46, name, 7, WHITE if on else TEXT_3, True, 0.9)


def l10(sc):
    """Command sheet: one big squircle holding a 3-column dashboard, dock on top of it."""
    sc.liquid(PAD, PAD, W - PAD * 2, H - PAD * 2, radius=48, tint=36, scrim=80,
              magnify=0.015, shadow=130)
    sc.rect(W / 2 - 34, PAD + 12, 68, 4, rgba(WHITE, 180), radius=2)

    sc.avatar(PAD + 56, PAD + 72, 24)
    sc.stext(PAD + 88, PAD + 52, "SAIFKHAN", 14, WHITE, True, 1.1)
    sc.stext(PAD + 88, PAD + 74, "SHADOW DRAGON ARSENAL · PREMIUM", 7.6, TEXT_3, True, 1.3)
    sc.liquid(W - PAD - 300, PAD + 48, 300, 46, radius=23, tint=42, scrim=24)
    sc.glyph("search", W - PAD - 274, PAD + 71, 11, TEXT_2)
    sc.text(W - PAD - 256, PAD + 64, "SEARCH INSTANCES", 7.8, TEXT_3, True, 1.1)

    top = PAD + 118
    col1 = 560
    # column 1: hero
    hero_panel(sc, PAD + 26, top, col1, 330, radius=34, compact=True)
    mods_strip(sc, PAD + 26, top + 348, col1, h=40)
    sc.liquid(PAD + 26, top + 404, col1, 178, radius=30, tint=28, scrim=72)
    sc.stext(PAD + 46, top + 418, "MOD STORE", 8.2, MAGENTA, True, 1.4)
    sc.stext(PAD + 46, top + 432, "Shadow Dragon Arsenal", 13.5, WHITE, True, 0.4)
    sc.text(PAD + 46, top + 454, "Sodium · Iris · Lithium · weekly drops", 8.2, TEXT_3, False)
    sc.pill(PAD + 46, top + 476, 118, 28, fill=MAGENTA, alpha=80, edge=rgba(MAGENTA, 205))
    sc.text(PAD + 66, top + 483, "BROWSE", 8, WHITE, True, 1.0)
    sc.pill(PAD + 176, top + 476, 118, 28)
    sc.text(PAD + 196, top + 483, "HUD KEYS", 8, TEXT_2, True, 1.0)

    # column 2: server + instances
    x2 = PAD + 26 + col1 + 22
    w2 = 430
    server_panel(sc, x2, top, w2, 150, radius=28)
    sc.liquid(x2, top + 166, w2, 240, radius=28, tint=30, scrim=72)
    sc.stext(x2 + 18, top + 180, "INSTANCES", 8.2, TEXT_3, True, 1.4)
    for i, (t, s2, a) in enumerate((("Fabric 1.21.10", "SHADOW PVP", True),
                                    ("LuciferMC SMP", "LIFESTEEL", False),
                                    ("CS Client", "1.8.9 PVP", False))):
        yy = top + 202 + i * 62
        sc.rect(x2 + 16, yy, w2 - 32, 54, rgba(WHITE, 40 if not a else 66), radius=16,
                outline=rgba(CYAN if a else WHITE, 200 if a else 96), width=1.1)
        sc.text(x2 + 32, yy + 11, t, 9.6, WHITE, True, 0.5)
        sc.text(x2 + 32, yy + 29, s2, 7.6, TEXT_3, True, 0.8)
        sc.glyph("play", x2 + w2 - 40, yy + 27, 9, CYAN if a else TEXT_3)
    sc.liquid(x2, top + 418, w2, 164, radius=28, tint=28, scrim=70)
    sc.stext(x2 + 18, top + 432, "GRAPHICS", 8.2, TEXT_3, True, 1.4)
    for i, (lab, val) in enumerate((("Renderer", "MobileGlues"), ("Shaders", "Complementary"),
                                    ("Resolution", "100 %"), ("FPS overlay", "ON"))):
        yy = top + 454 + i * 28
        sc.text(x2 + 18, yy, lab, 8.4, TEXT_3, True, 0.8)
        sc.text_end(x2 + w2 - 18, yy, val, 8.8, WHITE, True, 0.3)

    # column 3: stats + big launch
    x3 = x2 + w2 + 22
    w3 = W - PAD - 26 - x3
    sc.liquid(x3, top, w3, 150, radius=28, tint=30, scrim=70)
    sc.stext(x3 + 18, top + 14, "LIVE TELEMETRY", 8, TEXT_3, True, 1.4)
    for i, (lab, val) in enumerate((("FPS", "60"), ("RAM", "6.0 GB"))):
        sc.stext(x3 + 18 + i * (w3 / 2 - 9), top + 34, lab, 7.2, TEXT_3, True, 1.3)
        sc.stext(x3 + 18 + i * (w3 / 2 - 9), top + 48, val, 18, WHITE, True, 0.3)
    sc.rect(x3 + 18, top + 82, w3 - 36, 6, rgba(WHITE, 56), radius=3)
    sc.grad_rect(x3 + 18, top + 82, (w3 - 36) * 0.62, 6, lerp(CYAN, WHITE, 0.4), CYAN, radius=3)
    sc.stext(x3 + 18, top + 98, "VERSION 1.21.10", 8, TEXT_3, True, 1.1)
    sc.send(x3 + w3 - 18, top + 98, "FABRIC 0.16.9", 8, TEXT_3, True, 1.1)

    sc.liquid(x3, top + 166, w3, 246, radius=30, tint=34, scrim=68, magnify=0.05)
    sprite = base.skin_sprite(scale=10)
    th = 190
    tw = th * sprite.width / sprite.height
    sc.img.alpha_composite(sprite.resize((int(tw * S), int(th * S)), Image.LANCZOS),
                           (sc.s(x3 + w3 / 2 - tw / 2), sc.s(top + 186)))
    sc.redraw()
    sc.halo(x3 + w3 / 2, top + 300, 82, CYAN, 44)
    sc.grad_rect(x3 + 18, top + 366, w3 - 36, 36, lerp(CYAN, WHITE, 0.55), CYAN, radius=18)
    sc.glyph("play", x3 + 40, top + 384, 10, INK, 1.5)
    sc.text(x3 + 58, top + 377, "READY TO LAUNCH", 9.4, INK, True, 1.0)

    sc.liquid(x3, top + 428, w3, 154, radius=28, tint=28, scrim=70)
    sc.stext(x3 + 18, top + 442, "QUICK ACTIONS", 8.2, TEXT_3, True, 1.4)
    for i, (lab, kind) in enumerate((("NEW INSTANCE", "plus"), ("PROFILES", "profiles"),
                                     ("SERVERS", "servers"), ("CONTROLS", "controls"))):
        yy = top + 466 + i * 27
        sc.glyph(kind, x3 + 26, yy + 6, 9, CYAN)
        sc.text(x3 + 42, yy, lab, 8.6, WHITE, True, 0.8)
        sc.text_end(x3 + w3 - 18, yy, "›", 10, TEXT_3, True, 0)

    # footer strip: recent worlds, fills the band under the three columns
    fy = top + 592
    sc.liquid(PAD + 26, fy, W - PAD * 2 - 52, 74, radius=26, tint=28, scrim=64)
    sc.stext(PAD + 46, fy + 14, "RECENT WORLDS", 8.2, TEXT_3, True, 1.4)
    inner = W - PAD * 2 - 52 - 40
    for i, (nm, sub) in enumerate((("Lifesteel Base", "creative · spawn"), ("Shadow Arena", "pvp · 1v1"),
                                   ("Dragon Vault", "survival · day 42"))):
        tx = PAD + 46 + i * (inner / 3)
        sc.glyph("servers", tx + 8, fy + 44, 9, CYAN)
        sc.text(tx + 24, fy + 34, nm, 9.2, WHITE, True, 0.4)
        sc.text(tx + 24, fy + 47, sub, 7.2, TEXT_3, False, 0.3)

    dock_bar(sc, PAD + 26, H - PAD - 26 - 58, W - PAD * 2 - 52, 58)


LAYOUTS = [
    ("l01", "l01-floating-crystal", "FLOATING CRYSTAL", "top pill · hero left · instances right",
     "l01", (47, 233, 255), (217, 70, 239)),
    ("l02", "l02-bottom-sheet", "BOTTOM SHEET", "wallpaper first · one sheet holds all", "l02",
     (120, 220, 255), (255, 140, 220)),
    ("l03", "l03-side-rail", "SIDE RAIL", "vertical icon rail · wide hero", "l03", (90, 240, 220), (60, 180, 255)),
    ("l04", "l04-split-glass", "SPLIT GLASS", "two equal columns · dock across", "l04",
     (140, 190, 255), (220, 150, 255)),
    ("l05", "l05-island-hop", "ISLAND HOP", "floating islands · no big panels", "l05",
     (110, 255, 235), (255, 130, 200)),
    ("l06", "l06-tile-grid", "TILE GRID", "3x2 equal tiles · hero spans rows", "l06",
     (60, 220, 255), (190, 160, 255)),
    ("l07", "l07-settings-list", "SETTINGS LIST", "grouped rows · preview column", "l07",
     (200, 235, 255), (140, 210, 255)),
    ("l08", "l08-orbit", "ORBIT", "circular core · sections orbit", "l08", (0, 230, 255), (255, 100, 210)),
    ("l09", "l09-tab-bar", "TAB BAR", "hero top · ios tab bar bottom", "l09", (130, 240, 255), (200, 150, 255)),
    ("l10", "l10-command-sheet", "COMMAND SHEET", "one big sheet · 3-col dashboard", "l10",
     (47, 233, 255), (217, 70, 239)),
]

_GLOBALS = {"l01": l01, "l02": l02, "l03": l03, "l04": l04, "l05": l05,
            "l06": l06, "l07": l07, "l08": l08, "l09": l09, "l10": l10}


def render(key):
    bg = build_bg()
    sc = LiquidScreen(bg)
    _GLOBALS[key](sc)
    sc.finish()
    return sc.img.convert("RGB").resize((W, H), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) or None
    for num, slug, _name, _note, key, _c1, _c2 in LAYOUTS:
        if only and num not in only and slug not in only:
            continue
        img = render(key)
        path = OUT / f"{slug}.png"
        img.save(path)
        print("wrote", path.relative_to(ROOT), img.size)


if __name__ == "__main__":
    main()
