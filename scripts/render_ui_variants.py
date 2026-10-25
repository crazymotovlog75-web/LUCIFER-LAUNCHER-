#!/usr/bin/env python3
"""Render the LUCIFER LAUNCHER home screen exactly as it exists, in 10 colourways.

Nothing here is AI-generated art: the layout, the HUD plates, the server card, the
active-build card, the voxel character (the same skin geometry the launcher draws), the
crystal PLAY button and the dock are all drawn from code at 2x and downsampled. The only
image assets used are the ones already in the repo: the real background art
(`shadow-dragon-bg.webp`) and the real emblem (`shadow-dragon-emblem.png`), both simply
re-graded per colourway.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
MOCK = ROOT / "mockups"
OUT = MOCK / "variants"
S = 2  # supersample factor

W, H = 1600, 900
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# ---------------------------------------------------------------------------- palettes
PALETTES = [
    dict(slug="u01-abyss-teal", name="ABYSS TEAL", note="current theme, slightly richer",
         bg_dark=(4, 12, 22), bg_light=(150, 226, 236), bg_mix=0.42,
         accent=(0, 212, 255), accent2=(217, 70, 239),
         panel_a=(9, 18, 32), panel_b=(13, 24, 42), panel_a2=(10, 20, 36), panel_b2=(15, 28, 48),
         text=(248, 250, 252), muted=(148, 163, 184), live=(34, 197, 94)),
    dict(slug="u02-ember-forge", name="EMBER FORGE", note="molten orange on basalt",
         bg_dark=(16, 8, 6), bg_light=(246, 186, 120), bg_mix=0.46,
         accent=(255, 122, 24), accent2=(255, 205, 110),
         panel_a=(26, 15, 11), panel_b=(34, 19, 13), panel_a2=(30, 17, 12), panel_b2=(40, 22, 15),
         text=(255, 246, 238), muted=(196, 164, 140), live=(126, 217, 87)),
    dict(slug="u03-frost-lich", name="FROST LICH", note="aurora ice on steel",
         bg_dark=(6, 16, 30), bg_light=(206, 236, 252), bg_mix=0.44,
         accent=(125, 211, 252), accent2=(186, 230, 253),
         panel_a=(10, 20, 34), panel_b=(15, 28, 46), panel_a2=(12, 23, 38), panel_b2=(18, 33, 52),
         text=(244, 250, 255), muted=(160, 182, 202), live=(52, 211, 153)),
    dict(slug="u04-blood-moon", name="BLOOD MOON", note="crimson eclipse",
         bg_dark=(20, 5, 8), bg_light=(240, 130, 130), bg_mix=0.48,
         accent=(239, 68, 68), accent2=(251, 113, 133),
         panel_a=(28, 11, 14), panel_b=(38, 14, 18), panel_a2=(32, 12, 15), panel_b2=(44, 17, 22),
         text=(255, 244, 244), muted=(198, 158, 160), live=(248, 113, 113)),
    dict(slug="u05-gilded-dusk", name="GILDED DUSK", note="champagne gold on espresso",
         bg_dark=(18, 12, 8), bg_light=(246, 214, 160), bg_mix=0.46,
         accent=(245, 199, 107), accent2=(176, 125, 58),
         panel_a=(26, 20, 14), panel_b=(36, 27, 18), panel_a2=(30, 23, 16), panel_b2=(42, 32, 21),
         text=(255, 250, 242), muted=(190, 170, 146), live=(163, 230, 53)),
    dict(slug="u06-violet-void", name="VIOLET VOID", note="amethyst on deep space",
         bg_dark=(11, 6, 26), bg_light=(220, 190, 250), bg_mix=0.46,
         accent=(168, 85, 247), accent2=(232, 121, 249),
         panel_a=(18, 12, 36), panel_b=(26, 16, 50), panel_a2=(21, 13, 40), panel_b2=(30, 19, 56),
         text=(250, 245, 255), muted=(176, 160, 200), live=(74, 222, 128)),
    dict(slug="u07-toxic-jade", name="TOXIC JADE", note="sculk emerald + lime",
         bg_dark=(5, 16, 12), bg_light=(176, 236, 196), bg_mix=0.45,
         accent=(34, 197, 94), accent2=(163, 230, 53),
         panel_a=(9, 24, 18), panel_b=(13, 33, 24), panel_a2=(11, 27, 20), panel_b2=(16, 38, 28),
         text=(243, 255, 247), muted=(152, 184, 162), live=(163, 230, 53)),
    dict(slug="u08-midnight-sapphire", name="MIDNIGHT SAPPHIRE", note="storm blue on navy",
         bg_dark=(4, 10, 26), bg_light=(160, 196, 246), bg_mix=0.46,
         accent=(59, 130, 246), accent2=(96, 165, 250),
         panel_a=(9, 15, 34), panel_b=(13, 21, 46), panel_a2=(11, 18, 39), panel_b2=(16, 25, 52),
         text=(244, 248, 255), muted=(150, 168, 196), live=(52, 211, 153)),
    dict(slug="u09-cyber-nocturne", name="CYBER NOCTURNE", note="neon cyan + hot pink",
         bg_dark=(7, 9, 20), bg_light=(182, 226, 245), bg_mix=0.5,
         accent=(34, 211, 238), accent2=(255, 47, 179),
         panel_a=(12, 15, 28), panel_b=(17, 21, 38), panel_a2=(14, 17, 32), panel_b2=(20, 25, 43),
         text=(246, 251, 255), muted=(156, 172, 190), live=(74, 222, 128)),
    dict(slug="u10-bone-crypt", name="BONE CRYPT", note="bone sand + slate",
         bg_dark=(20, 19, 16), bg_light=(236, 226, 205), bg_mix=0.44,
         accent=(231, 214, 179), accent2=(154, 166, 178),
         panel_a=(26, 25, 22), panel_b=(35, 33, 29), panel_a2=(30, 29, 25), panel_b2=(40, 38, 33),
         text=(252, 250, 244), muted=(190, 184, 168), live=(163, 230, 53)),
]


# ---------------------------------------------------------------------------- helpers
def rgba(c, a=255):
    """Accept an (r,g,b) or (r,g,b,a) colour and return a 4-tuple."""
    c = tuple(c)
    return c if len(c) == 4 else (c[0], c[1], c[2], a)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, c1, c2):
    w, h = size
    img = Image.new("RGB", (1, h))
    for y in range(h):
        img.putpixel((0, y), lerp(c1, c2, y / max(1, h - 1)))
    return img.resize((w, h), Image.BILINEAR)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return m


class Canvas:
    def __init__(self, bg):
        self.img = bg.convert("RGBA")
        self.glows = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        self.gd = ImageDraw.Draw(self.glows)
        self.d = ImageDraw.Draw(self.img)

    # -- scaled coords
    @staticmethod
    def s(v):
        return int(round(v * S))

    def box(self, x, y, w, h):
        return [self.s(x), self.s(y), self.s(x + w) - 1, self.s(y + h) - 1]

    def panel(self, x, y, w, h, radius, c1, c2, border, border2=None, glow=None, alpha=236):
        pw, ph = self.s(w), self.s(h)
        grad = vgrad((pw, ph), c1, c2).convert("RGBA")
        grad.putalpha(rounded_mask((pw, ph), self.s(radius)).point(lambda v: int(v * alpha / 255)))
        self.img.alpha_composite(grad, (self.s(x), self.s(y)))
        d = ImageDraw.Draw(self.img)
        d.rounded_rectangle(self.box(x, y, w, h), self.s(radius),
                            outline=rgba(border, 255), width=max(1, self.s(1.2)))
        if border2:
            d.rounded_rectangle([self.s(x + 3), self.s(y + 3), self.s(x + w) - 4, self.s(y + h) - 4],
                                max(2, self.s(radius - 2)), outline=rgba(border2, 70),
                                width=max(1, self.s(1)))
        if glow:
            self.glow_box(x, y, w, h, radius, glow)

    def glow_box(self, x, y, w, h, radius, color, strength=110, spread=10):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(self.box(x, y, w, h), self.s(radius),
                                                outline=rgba(color, strength), width=self.s(spread))
        self.glows.alpha_composite(layer)

    def rect(self, x, y, w, h, fill, radius=0, outline=None, width=1):
        fill = rgba(fill) if fill is not None else None
        outline = rgba(outline) if outline is not None else None
        if radius:
            self.d.rounded_rectangle(self.box(x, y, w, h), self.s(radius), fill=fill,
                                     outline=outline, width=self.s(width) if outline else 0)
        else:
            self.d.rectangle(self.box(x, y, w, h), fill=fill,
                             outline=outline, width=self.s(width) if outline else 0)

    def grad_rect(self, x, y, w, h, c1, c2, radius=0):
        gw, gh = self.s(w), self.s(h)
        g = vgrad((gw, gh), c1, c2).convert("RGBA")
        if radius:
            g.putalpha(rounded_mask((gw, gh), self.s(radius)))
        self.img.alpha_composite(g, (self.s(x), self.s(y)))
        self.d = ImageDraw.Draw(self.img)

    def poly(self, points, fill=None, outline=None, width=1):
        pts = [(self.s(px), self.s(py)) for px, py in points]
        self.d.polygon(pts, fill=rgba(fill) if fill is not None else None)
        if outline:
            self.d.line(pts + [pts[0]], fill=rgba(outline), width=max(1, self.s(width)), joint="curve")

    def ellipse(self, x, y, w, h, fill=None, outline=None, width=1):
        self.d.ellipse(self.box(x, y, w, h),
                       fill=rgba(fill) if fill is not None else None,
                       outline=rgba(outline) if outline is not None else None,
                       width=max(1, self.s(width)) if outline else 0)

    @staticmethod
    def font(size, bold=True):
        return ImageFont.truetype(FONT_B if bold else FONT_R, int(round(size * S)))

    def text(self, x, y, s, size, color, bold=True, tracking=0.0, anchor_left=True):
        f = self.font(size, bold)
        cx = self.s(x)
        if tracking:
            for ch in s:
                self.d.text((cx, self.s(y)), ch, font=f, fill=rgba(color))
                cx += self.d.textlength(ch, font=f) + tracking * S
            return cx
        self.d.text((cx, self.s(y)), s, font=f, fill=rgba(color))
        return cx + self.d.textlength(s, font=f)

    def text_center(self, cx, y, s, size, color, bold=True, tracking=0.0):
        f = self.font(size, bold)
        width = self.d.textlength(s, font=f) + tracking * S * max(0, len(s) - 1)
        return self.text(cx - width / (2 * S), y, s, size, color, bold, tracking)

    def text_right(self, rx, y, s, size, color, bold=True, tracking=0.0):
        f = self.font(size, bold)
        width = (self.d.textlength(s, font=f) + tracking * S * max(0, len(s) - 1)) / S
        return self.text(rx - width, y, s, size, color, bold, tracking)

    def glow(self, cx, cy, r, color, strength=90):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(
            [self.s(cx - r), self.s(cy - r), self.s(cx + r), self.s(cy + r)],
            fill=rgba(color, strength))
        self.glows.alpha_composite(layer)

    def finish(self):
        blurred = self.glows.filter(ImageFilter.GaussianBlur(self.s(9)))
        self.img.alpha_composite(blurred)
        self.img.alpha_composite(self.glows.filter(ImageFilter.GaussianBlur(self.s(2))))


from PIL import ImageFont  # noqa: E402  (imported for Canvas.font)


# ---------------------------------------------------------------------------- background
def build_background(p):
    art = Image.open(MOCK / "shadow-dragon-bg.webp").convert("RGB")
    art = ImageOps.fit(art, (W * S, H * S), method=Image.LANCZOS)

    grey = ImageOps.grayscale(art)
    grey = ImageOps.autocontrast(grey, cutoff=1)
    toned = ImageOps.colorize(grey, black=p["bg_dark"], white=p["bg_light"],
                              mid=p["accent2"] if sum(p["accent2"]) > sum(p["accent"]) else p["accent"])
    toned = ImageEnhance.Color(toned).enhance(1.15)
    # Keep some of the original painting's own colour so it still reads as hand-drawn art.
    art2 = ImageEnhance.Color(art).enhance(1.05)
    bg = Image.blend(toned, art2, p["bg_mix"])

    # readability: darken the middle band where the UI cards sit, plus a soft vignette
    shade = Image.new("L", bg.size, 0)
    sd = ImageDraw.Draw(shade)
    sd.rectangle([0, 0, bg.size[0], bg.size[1]], fill=0)
    sd.ellipse([-bg.size[0] * 0.25, bg.size[1] * 0.10, bg.size[0] * 0.55, bg.size[1] * 1.15], fill=150)
    sd.ellipse([bg.size[0] * 0.72, bg.size[1] * 0.15, bg.size[0] * 1.3, bg.size[1] * 1.2], fill=120)
    sd.rectangle([0, bg.size[1] * 0.30, bg.size[0], bg.size[1] * 0.92], fill=95)
    shade = shade.filter(ImageFilter.GaussianBlur(bg.size[0] // 26))
    dark = Image.new("RGB", bg.size, p["bg_dark"])
    bg = Image.composite(dark, bg, shade.point(lambda v: int(v * 0.78)))

    # accent glow behind the pedestal, tinted per colourway
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([bg.size[0] * 0.40, bg.size[1] * 0.30, bg.size[0] * 0.66, bg.size[1] * 0.95],
               fill=p["accent"] + (70,))
    gd.ellipse([bg.size[0] * 0.58, bg.size[1] * 0.55, bg.size[0] * 0.80, bg.size[1] * 0.98],
               fill=p["accent2"] + (46,))
    glow = glow.filter(ImageFilter.GaussianBlur(bg.size[0] // 18))
    bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")
    return bg


# ---------------------------------------------------------------------------- widgets
def hero(cv, cx, base_y, scale, p):
    """The launcher's voxel character, exactly the same geometry as the app, re-tinted."""
    def X(v):
        return cx + (v - 60) * scale

    def Y(v):
        return base_y + (v - 180) * scale

    accent, accent2 = p["accent"], p["accent2"]
    deep = lerp(p["panel_a"], (0, 0, 0), 0.35)
    armor = lerp(p["panel_b"], (0, 0, 0), 0.25)

    # pedestal
    cv.ellipse(X(14), Y(157), 92 * scale, 18 * scale, fill=deep)
    cv.ellipse(X(14), Y(157), 92 * scale, 18 * scale, outline=accent, width=1.6)
    cv.ellipse(X(28), Y(161), 64 * scale, 10 * scale, fill=accent2 + (140,))
    cv.glow(cx, base_y, 150 * scale, accent, 55)

    # cape
    cv.poly([(X(34), Y(58)), (X(86), Y(58)), (X(96), Y(144)), (X(24), Y(144))],
            fill=lerp(accent2, (0, 0, 0), 0.55), outline=accent2, width=1.5)

    # legs
    for x in (39, 62):
        cv.rect(X(x), Y(112), 19 * scale, 50 * scale, fill=armor, outline=accent, width=1.2)

    # torso
    cv.rect(X(36), Y(60), 48 * scale, 52 * scale, fill=lerp(armor, (0, 0, 0), 0.2),
            outline=accent, width=1.5)
    cv.poly([(X(60), Y(68)), (X(68), Y(80)), (X(60), Y(94)), (X(52), Y(80))], fill=accent)

    # arms + blades
    for x in (18, 86):
        cv.rect(X(x), Y(62), 16 * scale, 46 * scale, fill=lerp(armor, accent2, 0.10),
                outline=accent2, width=1.2)
    cv.poly([(X(18), Y(104)), (X(2), Y(138)), (X(12), Y(140)), (X(28), Y(108))], fill=accent)
    cv.poly([(X(102), Y(104)), (X(118), Y(138)), (X(108), Y(140)), (X(92), Y(108))], fill=accent2)

    # head
    cv.rect(X(38), Y(18), 44 * scale, 42 * scale, fill=lerp(armor, (0, 0, 0), 0.45),
            outline=lerp(accent, accent2, 0.5), width=1.8)
    cv.poly([(X(38), Y(26)), (X(24), Y(6)), (X(34), Y(18))], fill=accent)
    cv.poly([(X(82), Y(26)), (X(96), Y(6)), (X(86), Y(18))], fill=accent2)
    cv.rect(X(44), Y(36), 11 * scale, 5 * scale, fill=accent)
    cv.rect(X(65), Y(36), 11 * scale, 5 * scale, fill=accent)


def crystal_play(cv, cx, cy, r, p):
    accent, accent2 = p["accent"], p["accent2"]
    cv.glow(cx, cy, r * 1.55, accent2, 60)
    cv.glow(cx, cy, r * 1.15, accent, 70)
    cv.ellipse(cx - r, cy - r, 2 * r, 2 * r, fill=lerp(p["panel_a"], (0, 0, 0), 0.2))
    # faceted crystal body
    import math
    facets = []
    for i in range(8):
        a = math.pi / 8 + i * math.pi / 4
        facets.append((cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9))
    for i in range(8):
        p1, p2 = facets[i], facets[(i + 1) % 8]
        shade = 0.30 + 0.22 * (i % 4)
        cv.poly([(cx, cy), p1, p2], fill=lerp(accent2, accent, shade))
    for i in range(8):
        p1, p2 = facets[i], facets[(i + 1) % 8]
        cv.d.line([(cv.s(p1[0]), cv.s(p1[1])), (cv.s(p2[0]), cv.s(p2[1]))],
                  fill=rgba(accent, 110), width=max(1, cv.s(1)))
    cv.ellipse(cx - r, cy - r, 2 * r, 2 * r, outline=accent2, width=2.2)
    cv.ellipse(cx - r * 1.1, cy - r * 1.1, 2.2 * r, 2.2 * r, outline=accent + (110,), width=1.2)
    # play triangle
    cv.poly([(cx - r * 0.20, cy - r * 0.28), (cx + r * 0.34, cy), (cx - r * 0.20, cy + r * 0.28)],
            fill=(255, 255, 255, 235))
    cv.text_center(cx, cy + r * 0.44, "PLAY", 15, (255, 255, 255), tracking=1.4)


def icon_home(cv, cx, cy, size, color):
    cv.poly([(cx, cy - size), (cx + size, cy - size * 0.05), (cx + size * 0.62, cy - size * 0.05),
             (cx + size * 0.62, cy + size * 0.85), (cx - size * 0.62, cy + size * 0.85),
             (cx - size * 0.62, cy - size * 0.05), (cx - size, cy - size * 0.05)], fill=color)


def icon_person(cv, cx, cy, size, color):
    cv.ellipse(cx - size * 0.42, cy - size, size * 0.84, size * 0.84, fill=color)
    cv.ellipse(cx - size * 0.9, cy + size * 0.02, size * 1.8, size * 1.35, fill=color)


def icon_cube(cv, cx, cy, size, color):
    cv.poly([(cx, cy - size), (cx + size, cy - size * 0.45), (cx, cy + size * 0.1),
             (cx - size, cy - size * 0.45)], fill=color)
    cv.poly([(cx - size, cy - size * 0.45), (cx, cy + size * 0.1), (cx, cy + size),
             (cx - size, cy + size * 0.45)], fill=lerp(color[:3], (0, 0, 0), 0.28))
    cv.poly([(cx + size, cy - size * 0.45), (cx, cy + size * 0.1), (cx, cy + size),
             (cx + size, cy + size * 0.45)], fill=lerp(color[:3], (0, 0, 0), 0.15))


def icon_server(cv, cx, cy, size, color):
    for dy in (-0.75, 0.25):
        cv.rect(cx - size, cy + size * dy, 2 * size, size * 0.7, fill=color, radius=1.5)


def icon_pad(cv, cx, cy, size, color):
    cv.ellipse(cx - size, cy - size * 0.42, 2 * size, size * 1.05, fill=color)
    cv.rect(cx - size * 0.28, cy - size * 0.16, size * 0.56, size * 0.32, fill=(0, 0, 0, 0))


def icon_slime(cv, cx, cy, size, color):
    cv.rect(cx - size * 0.9, cy - size * 0.85, size * 1.8, size * 1.55, fill=color, radius=2)
    cv.rect(cx - size * 0.45, cy - size * 0.35, size * 0.3, size * 0.3,
            fill=lerp(color[:3], (0, 0, 0), 0.6), radius=1)
    cv.rect(cx + size * 0.15, cy - size * 0.35, size * 0.3, size * 0.3,
            fill=lerp(color[:3], (0, 0, 0), 0.6), radius=1)


def icon_gear(cv, cx, cy, size, color):
    import math
    for i in range(6):
        a = i * math.pi / 3
        cv.rect(cx + math.cos(a) * size * 0.62 - size * 0.2,
                cy + math.sin(a) * size * 0.62 - size * 0.2,
                size * 0.4, size * 0.4, fill=color, radius=1)
    cv.ellipse(cx - size * 0.62, cy - size * 0.62, size * 1.24, size * 1.24, fill=color)
    cv.ellipse(cx - size * 0.26, cy - size * 0.26, size * 0.52, size * 0.52,
               fill=lerp(color[:3], (0, 0, 0), 0.55))


# ---------------------------------------------------------------------------- screen
def render(p):
    bg = build_background(p)
    cv = Canvas(bg)

    M = 22
    accent, accent2 = p["accent"], p["accent2"]
    text, muted = p["text"], p["muted"]
    panel_text = text

    # ---------------------------------------------------------------- HUD
    hud_y, hud_h = 18, 54
    cv.panel(M, hud_y, 300, hud_h, 12, p["panel_a2"], p["panel_b2"], accent, accent2, glow=accent)
    emblem = Image.open(MOCK / "shadow-dragon-emblem.png").convert("RGBA")
    eh = int((hud_h - 18) * S)
    emblem = emblem.resize((int(emblem.width * eh / emblem.height), eh), Image.LANCZOS)
    cv.img.alpha_composite(emblem, (cv.s(M + 12), cv.s(hud_y + 9)))
    cv.text(M + 24 + eh / S, hud_y + 13, "LUCIFER", 23, text, tracking=1.4)

    tel_w, tel_h = 420, 44
    cv.panel((W - tel_w) / 2, hud_y + 5, tel_w, tel_h, 22, p["panel_a2"], p["panel_b2"],
             accent + (255,), None, glow=accent2)
    tx = (W - tel_w) / 2 + 26
    tx = cv.text(tx, hud_y + 18, "VULKAN ZINK", 11, accent, tracking=0.9) / S + 12
    cv.text(tx, hud_y + 17, "·", 13, muted)
    tx = cv.text(tx + 12, hud_y + 18, "1.21 PACK ON", 11, panel_text, tracking=0.9) / S + 12
    cv.text(tx, hud_y + 17, "·", 13, muted)
    cv.text(tx + 12, hud_y + 18, "6.0 GB RAM", 11, accent2, tracking=0.9)

    user_w = 232
    ux = W - M - user_w
    cv.panel(ux, hud_y, user_w, hud_h, 12, p["panel_a2"], p["panel_b2"], accent, accent2, glow=accent)
    # avatar block (pixel face, launcher-style)
    av_s = 34
    ax, ay = ux + 12, hud_y + 10
    cv.rect(ax, ay, av_s, av_s, fill=lerp(p["panel_b"], (0, 0, 0), 0.35), radius=6, outline=accent2 + (200,))
    cv.rect(ax + 7, ay + 8, 6, 6, fill=accent2)
    cv.rect(ax + 21, ay + 8, 6, 6, fill=accent2)
    cv.rect(ax + 12, ay + 21, 10, 4, fill=lerp(accent, text, 0.35))
    cv.text(ax + av_s + 12, hud_y + 13, "SAIFKHAN", 15, text, tracking=0.8)
    cv.text_right(ux + user_w - 12, hud_y + 34, "MSA", 9, accent2, tracking=0.8)

    # ---------------------------------------------------------------- stage geometry
    stage_top = hud_y + hud_h + 16
    dock_h = 62
    dock_y = H - 18 - dock_h
    stage_bottom = dock_y - 16
    left_w = 470
    right_w = 300
    gap = 18
    center_x = M + left_w + gap
    center_w = W - 2 * M - left_w - right_w - 2 * gap
    right_x = W - M - right_w

    # ---------------------------------------------------------------- left: server card
    sc_x, sc_y, sc_w = M, stage_top, left_w
    sc_h = 148
    cv.panel(sc_x, sc_y, sc_w, sc_h, 14, p["panel_a"], p["panel_b"], accent, accent2, glow=accent)
    cv.text(sc_x + 16, sc_y + 14, "LUCIFERMC — LIFESTEEL SMP", 13, text, tracking=0.6)
    badge = "OFFICIAL"
    bw = cv.d.textlength(badge, font=cv.font(9)) / S + 16
    cv.grad_rect(sc_x + sc_w - 16 - bw, sc_y + 13, bw, 18, lerp(accent2, (0, 0, 0), 0.12), accent2, radius=5)
    cv.text_center(sc_x + sc_w - 16 - bw / 2, sc_y + 16, badge, 9, (10, 10, 14), tracking=0.5)

    cv.text(sc_x + 16, sc_y + 42, "play.lucifermc.fun", 11.5, accent, bold=False)
    cv.text_right(sc_x + sc_w - 16, sc_y + 42, "LIVE · 24ms", 11, p["live"], tracking=0.4)
    cv.ellipse(sc_x + sc_w - 16 - cv.d.textlength("LIVE · 24ms", font=cv.font(11)) / S - 12,
               sc_y + 47, 6, 6, fill=p["live"])

    by = sc_y + sc_h - 44
    join_w = 150
    cv.grad_rect(sc_x + 16, by, join_w, 30, lerp(accent, text, 0.30), accent, radius=8)
    cv.text_center(sc_x + 16 + join_w / 2, by + 8, "JOIN", 12, lerp(p["panel_a"], (0, 0, 0), 0.6), tracking=1.6)
    pill_w = (sc_w - 32 - join_w - 20) / 2
    for i, label in enumerate(("DISCORD", "WIKI")):
        px = sc_x + 16 + join_w + 10 + i * (pill_w + 10)
        cv.panel(px, by, pill_w, 30, 8, p["panel_a2"], p["panel_b2"], accent + (140,), None, alpha=250)
        cv.text_center(px + pill_w / 2, by + 9, label, 10, text, tracking=0.9)

    # ---------------------------------------------------------------- left: active build
    ab_y = sc_y + sc_h + gap
    ab_h = stage_bottom - ab_y
    cv.panel(M, ab_y, sc_w, ab_h, 14, p["panel_a"], p["panel_b"], accent, accent2, glow=accent2)
    cv.text(M + 16, ab_y + 14, "ACTIVE BUILD // VERSION", 9, accent2, tracking=1.4)
    cv.text(M + 16, ab_y + 30, "Fabric 1.21.4 — Shadow PvP", 17, text, tracking=0.4)
    cv.text(M + 16, ab_y + 54, "Fabric Loader 0.16 · Sodium + Iris · 6.0 GB RAM", 10.5, accent, bold=False)

    chips = [("Fabric 1.21.4", "Mods: 42 · Ready", True),
             ("LuciferMC SMP", "Mods: 28 · Official", False),
             ("Forge 1.20.1", "Mods: 64 · Heavy", False)]
    chip_gap = 10
    chip_w = (sc_w - 32 - chip_gap * 2) / 3
    chip_h = 52
    chip_y = ab_y + ab_h - chip_h - 16
    for i, (title, sub, sel) in enumerate(chips):
        cx0 = M + 16 + i * (chip_w + chip_gap)
        if sel:
            cv.panel(cx0, chip_y, chip_w, chip_h, 10, lerp(accent, p["panel_b"], 0.72),
                     lerp(accent2, p["panel_b"], 0.78), accent, None, glow=accent, alpha=245)
        else:
            cv.panel(cx0, chip_y, chip_w, chip_h, 10, p["panel_a2"], p["panel_b2"],
                     accent2 + (120,), None, alpha=235)
        cv.text(cx0 + 10, chip_y + 9, title, 10.5, text, tracking=0.2)
        cv.text(cx0 + 10, chip_y + 27, sub, 8.5, accent if sel else muted, bold=False)

    # ---------------------------------------------------------------- center: character
    stage_cy = (stage_top + stage_bottom) / 2
    hero_scale = 1.55
    hero(cv, center_x + center_w / 2, stage_cy + 168, hero_scale, p)

    skin_w, skin_h = 168, 30
    sx = center_x + (center_w - skin_w) / 2
    sy = stage_bottom - skin_h
    cv.panel(sx, sy, skin_w, skin_h, 8, p["panel_a2"], p["panel_b2"], accent + (170,), None, alpha=240)
    cv.text_center(sx + skin_w / 2, sy + 8, "SKIN STUDIO", 10, text, tracking=1.2)

    # ---------------------------------------------------------------- right column
    ar_h = 92
    cv.panel(right_x, stage_top, right_w, ar_h, 14, p["panel_a"], p["panel_b"], accent, accent2, glow=accent2)
    cv.text(right_x + 14, stage_top + 13, "SHADOW DRAGON ARSENAL", 8.5, accent, tracking=1.3)
    pw = (right_w - 28 - 10) / 2
    for i, label in enumerate(("144 FPS BOOST", "RAM: 6.0 GB")):
        px = right_x + 14 + i * (pw + 10)
        if i == 0:
            cv.panel(px, stage_top + 34, pw, 42, 9, lerp(accent, p["panel_b"], 0.6),
                     lerp(accent2, p["panel_b"], 0.7), accent, None, glow=accent, alpha=245)
        else:
            cv.panel(px, stage_top + 34, pw, 42, 9, p["panel_a2"], p["panel_b2"],
                     accent2 + (130,), None, alpha=240)
        cv.text_center(px + pw / 2, stage_top + 47, label, 9, text, tracking=0.4)

    play_top = stage_top + ar_h + gap
    play_h = stage_bottom - play_top
    play_cx = right_x + right_w / 2
    play_cy = play_top + play_h / 2 + 6
    crystal_play(cv, play_cx, play_cy, min(right_w / 2 - 12, play_h / 2 - 26), p)
    cv.text_center(play_cx, play_top + play_h - 22, "FABRIC 1.21.4", 9, accent, tracking=1.0)

    # ---------------------------------------------------------------- dock
    dock_w = 900
    dock_x = (W - dock_w) / 2
    cv.panel(dock_x, dock_y, dock_w, dock_h, 14, p["panel_a"], p["panel_b"], accent, accent2, glow=accent)
    tabs = [("HOME", icon_home, True), ("PROFILES", icon_person, False), ("MODS", icon_cube, False),
            ("SERVERS", icon_server, False), ("CONTROLS", icon_pad, False), ("SKINS", icon_slime, False),
            ("SETTINGS", icon_gear, False)]
    tab_w = dock_w / len(tabs)
    for i, (label, icon, active) in enumerate(tabs):
        tcx = dock_x + tab_w * i + tab_w / 2
        color = accent if active else muted
        icon(cv, tcx, dock_y + 22, 7, color if active else rgba(color, 200))
        cv.text_center(tcx, dock_y + 38, label, 8.5, text if active else muted, tracking=0.7)
        if active:
            cv.rect(tcx - 26, dock_y + dock_h - 8, 52, 3, fill=accent, radius=2)

    # crystal end caps on the dock
    for side in (-1, 1):
        ex = dock_x + (0 if side < 0 else dock_w)
        cv.poly([(ex, dock_y + 12), (ex + side * 16, dock_y + dock_h / 2), (ex, dock_y + dock_h - 12),
                 (ex - side * 8, dock_y + dock_h / 2)],
                fill=lerp(accent, p["panel_b"], 0.55), outline=accent2, width=1.2)

    cv.finish()
    out = cv.img.convert("RGB").resize((W, H), Image.LANCZOS)
    path = OUT / f"{p['slug']}.png"
    out.save(path, "PNG", optimize=True)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:] or None
    for p in PALETTES:
        if only and p["slug"] not in only:
            continue
        path = render(p)
        print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
