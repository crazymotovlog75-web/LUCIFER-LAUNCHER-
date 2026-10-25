#!/usr/bin/env python3
"""Render the LUCIFER LAUNCHER home screen exactly as the app draws it, in colourways.

This is not AI concept art. The screen is reconstructed from the app's own resources:

* layout structure  -> res/layout-land/activity_pojav_launcher.xml
                       (header plates + nav items + account plate + dock)
                    -> res/layout/fragment_right_pane_home.xml
                       (server card, active-build card, hero stage, launch reactor)
* panel shapes      -> bg_sd_hud_plate.xml, bg_sd_crystal_card.xml, bg_sd_dock_shell.xml
* stage art         -> bg_sd_shadow_flame_stage.xml (aura, flames, pedestal, spikes)
* PLAY reactor      -> ic_sd_reactor_idle.xml (crystal spikes + hexagonal plasma core)
* character         -> the real skin atlas, composed with the exact same front-view
                       algorithm as MinecraftSkinPreviewRenderer.renderFront()

Only the palette changes between the ten renders: accent (sd_cyan), secondary accent
(sd_magenta), panel tint and a gentle background re-grade.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MOCK = ROOT / "mockups"
OUT = MOCK / "variants"
SKIN = MOCK / "assets" / "skin-default.png"
WALL = MOCK / "backgrounds" / "bg10-abyss-teal.jpg"
EMBLEM = MOCK / "shadow-dragon-emblem.png"

W, H = 1600, 900
S = 2

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def rgba(c, a=255):
    c = tuple(c)
    return c if len(c) == 4 else (c[0], c[1], c[2], a)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(size, c1, c2, c3=None):
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        if c3 is None:
            col.putpixel((0, y), lerp(c1, c2, t))
        elif t < 0.5:
            col.putpixel((0, y), lerp(c1, c2, t * 2))
        else:
            col.putpixel((0, y), lerp(c2, c3, (t - 0.5) * 2))
    return col.resize((w, h), Image.BILINEAR)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return m


# --------------------------------------------------------------------------- palettes
PALETTES = [
    dict(slug="v01-abyss-teal", name="ABYSS TEAL", note="current launcher palette",
         cyan=(47, 233, 255), magenta=(217, 70, 239), panel=(6, 17, 26), panel_hi=(13, 36, 46),
         wall_mix=0.0),
    dict(slug="v02-ember-forge", name="EMBER FORGE", note="molten orange accent",
         cyan=(255, 138, 46), magenta=(255, 196, 84), panel=(24, 12, 8), panel_hi=(48, 24, 14),
         wall_mix=0.58),
    dict(slug="v03-frost-lich", name="FROST LICH", note="ice blue accent",
         cyan=(140, 220, 255), magenta=(186, 214, 255), panel=(8, 18, 30), panel_hi=(18, 38, 58),
         wall_mix=0.50),
    dict(slug="v04-blood-moon", name="BLOOD MOON", note="crimson accent",
         cyan=(255, 86, 92), magenta=(255, 128, 156), panel=(24, 8, 12), panel_hi=(46, 16, 22),
         wall_mix=0.60),
    dict(slug="v05-gilded-dusk", name="GILDED DUSK", note="champagne gold accent",
         cyan=(248, 208, 122), magenta=(196, 138, 66), panel=(22, 16, 10), panel_hi=(44, 33, 20),
         wall_mix=0.58),
    dict(slug="v06-violet-void", name="VIOLET VOID", note="amethyst accent",
         cyan=(178, 140, 255), magenta=(232, 121, 249), panel=(14, 8, 28), panel_hi=(30, 18, 54),
         wall_mix=0.50),
    dict(slug="v07-toxic-jade", name="TOXIC JADE", note="emerald accent",
         cyan=(88, 230, 160), magenta=(163, 230, 53), panel=(8, 22, 16), panel_hi=(16, 42, 30),
         wall_mix=0.52),
    dict(slug="v08-midnight-sapphire", name="MIDNIGHT SAPPHIRE", note="sapphire accent",
         cyan=(96, 165, 250), magenta=(129, 140, 248), panel=(8, 14, 30), panel_hi=(16, 28, 54),
         wall_mix=0.50),
    dict(slug="v09-cyber-nocturne", name="CYBER NOCTURNE", note="neon cyan + hot pink",
         cyan=(38, 231, 255), magenta=(255, 62, 176), panel=(10, 12, 24), panel_hi=(20, 24, 42),
         wall_mix=0.42),
    dict(slug="v10-bone-crypt", name="BONE CRYPT", note="bone + slate accent",
         cyan=(236, 224, 196), magenta=(160, 172, 184), panel=(22, 21, 18), panel_hi=(40, 38, 32),
         wall_mix=0.55),
]


# --------------------------------------------------------------------------- canvas
class Screen:
    def __init__(self, bg):
        self.img = bg.convert("RGBA")
        self.glow = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        self.gd = ImageDraw.Draw(self.glow)
        self.d = ImageDraw.Draw(self.img)

    def s(self, v):
        return int(round(v * S))

    def box(self, x, y, w, h):
        return [self.s(x), self.s(y), self.s(x + w) - 1, self.s(y + h) - 1]

    def redraw(self):
        self.d = ImageDraw.Draw(self.img)

    # ---- panels ----------------------------------------------------------
    def card(self, x, y, w, h, p, radius=13, accent_alpha=255, glow=False):
        """bg_sd_crystal_card: 315deg gradient, outer stroke, inner stroke, corner shards."""
        pw, ph = self.s(w), self.s(h)
        g = vgrad((pw, ph), lerp(p["panel"], (0, 0, 0), 0.05),
                  p["panel_hi"], lerp(p["panel"], (0, 0, 0), 0.02)).convert("RGBA")
        mask = rounded_mask((pw, ph), self.s(radius)).point(lambda v: int(v * 236 / 255))
        g.putalpha(mask)
        self.img.alpha_composite(g, (self.s(x), self.s(y)))
        self.redraw()

        self.d.rounded_rectangle(self.box(x, y, w, h), self.s(radius),
                                 outline=rgba(p["cyan"], int(accent_alpha * 0.62)),
                                 width=max(1, self.s(1.4)))
        self.d.rounded_rectangle(self.box(x + 2, y + 2, w - 4, h - 4), self.s(radius - 1),
                                 outline=rgba(p["magenta"], 85), width=max(1, self.s(1)))
        if glow:
            self.soft_box(x, y, w, h, radius, p["cyan"], 60, 8)
        # corner shards
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1),
                               (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
            L = 15 if sy > 0 else 13
            self.poly([(cx, cy + sy * L * 0.55), (cx + sx * L * 0.55, cy),
                       (cx + sx * L * 0.78, cy + sy * 1.4), (cx, cy + sy * L * 0.62)],
                      fill=rgba(p["cyan"], 235))
            self.poly([(cx + sx * 1.6, cy + sy * L * 0.30), (cx + sx * L * 0.34, cy + sy * 1.6),
                       (cx + sx * L * 0.40, cy + sy * L * 0.62), (cx + sx * 1.6, cy + sy * L * 0.52)],
                      fill=rgba(p["magenta"], 235))

    def plate(self, x, y, w, h, p, radius=10):
        """bg_sd_hud_plate: horizontal gradient + 1.5dp cyan stroke + inner magenta."""
        pw, ph = self.s(w), self.s(h)
        g = vgrad((pw, ph), lerp(p["panel"], p["cyan"], 0.05), lerp(p["panel"], p["magenta"], 0.10),
                  lerp(p["panel"], p["cyan"], 0.05)).convert("RGBA")
        mask = rounded_mask((pw, ph), self.s(radius)).point(lambda v: int(v * 235 / 255))
        g.putalpha(mask)
        self.img.alpha_composite(g, (self.s(x), self.s(y)))
        self.redraw()
        self.d.rounded_rectangle(self.box(x, y, w, h), self.s(radius),
                                 outline=rgba(p["cyan"], 170), width=max(1, self.s(1.5)))
        self.d.rounded_rectangle(self.box(x + 1.5, y + 1.5, w - 3, h - 3), self.s(radius - 1),
                                 outline=rgba(p["magenta"], 85), width=max(1, self.s(1)))
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y + h, -1, -1)):
            L = 13
            self.poly([(cx, cy + sy * L * 0.5), (cx + sx * L * 0.5, cy),
                       (cx + sx * L * 0.8, cy + sy * 1.2), (cx, cy + sy * L * 0.56)],
                      fill=rgba(p["cyan"], 240))

    def soft_box(self, x, y, w, h, radius, color, strength=70, spread=9):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(self.box(x, y, w, h), self.s(radius),
                                                outline=rgba(color, strength),
                                                width=self.s(spread))
        self.glow.alpha_composite(layer)

    # ---- primitives ------------------------------------------------------
    def _alpha_ok(self, *colors):
        """True when every colour is fully opaque, i.e. safe to draw straight on the layer."""
        for c in colors:
            if c is None:
                continue
            c = rgba(c)
            if c[3] != 255:
                return False
        return True

    def _layer(self, fn):
        """Draw through a transparent layer so alpha is composited, never overwritten."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer))
        self.img.alpha_composite(layer)
        self.redraw()

    def rect(self, x, y, w, h, fill, radius=0, outline=None, width=1):
        f = rgba(fill) if fill is not None else None
        o = rgba(outline) if outline is not None else None
        if not self._alpha_ok(fill, outline):
            def draw(d):
                if radius:
                    d.rounded_rectangle(self.box(x, y, w, h), self.s(radius), fill=f, outline=o,
                                        width=max(1, self.s(width)) if o else 0)
                else:
                    d.rectangle(self.box(x, y, w, h), fill=f, outline=o,
                                width=max(1, self.s(width)) if o else 0)
            return self._layer(draw)
        if radius:
            self.d.rounded_rectangle(self.box(x, y, w, h), self.s(radius), fill=f, outline=o,
                                     width=max(1, self.s(width)) if o else 0)
        else:
            self.d.rectangle(self.box(x, y, w, h), fill=f, outline=o,
                             width=max(1, self.s(width)) if o else 0)

    def grad_rect(self, x, y, w, h, c1, c2, radius=0):
        gw, gh = self.s(w), self.s(h)
        g = vgrad((gw, gh), c1, c2).convert("RGBA")
        if radius:
            g.putalpha(rounded_mask((gw, gh), self.s(radius)))
        self.img.alpha_composite(g, (self.s(x), self.s(y)))
        self.redraw()

    def poly(self, pts, fill=None, outline=None, width=1):
        pts = [(self.s(px), self.s(py)) for px, py in pts]
        f = rgba(fill) if fill is not None else None
        o = rgba(outline) if outline is not None else None

        def draw(d):
            d.polygon(pts, fill=f)
            if o:
                d.line(pts + [pts[0]], fill=o, width=max(1, self.s(width)), joint="curve")

        if not self._alpha_ok(fill, outline):
            return self._layer(draw)
        draw(self.d)

    def ellipse(self, x, y, w, h, fill=None, outline=None, width=1):
        f = rgba(fill) if fill is not None else None
        o = rgba(outline) if outline is not None else None

        def draw(d):
            d.ellipse(self.box(x, y, w, h), fill=f, outline=o,
                      width=max(1, self.s(width)) if o else 0)

        if not self._alpha_ok(fill, outline):
            return self._layer(draw)
        draw(self.d)

    def flush_glow(self):
        """Bake the pending halo into the layer, so shapes drawn after it stay crisp."""
        if self.glow.getbbox() is None:
            return
        self.img.alpha_composite(self.glow.filter(ImageFilter.GaussianBlur(self.s(9))))
        self.img.alpha_composite(self.glow.filter(ImageFilter.GaussianBlur(self.s(2))))
        self.glow = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        self.gd = ImageDraw.Draw(self.glow)
        self.redraw()

    def halo(self, cx, cy, r, color, strength=60, blur=None):
        """A soft radial wash drawn straight into the layer with a wide blur."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([self.s(cx - r), self.s(cy - r),
                                       self.s(cx + r), self.s(cy + r)],
                                      fill=rgba(color, strength))
        layer = layer.filter(ImageFilter.GaussianBlur(blur if blur else max(8, self.s(r * 0.32))))
        self.img.alpha_composite(layer)
        self.redraw()

    def blur(self, cx, cy, r, color, strength=90):
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse([self.s(cx - r), self.s(cy - r),
                                       self.s(cx + r), self.s(cy + r)], fill=rgba(color, strength))
        self.glow.alpha_composite(layer)

    # ---- text ------------------------------------------------------------
    def font(self, size, bold=True):
        return ImageFont.truetype(FONT_B if bold else FONT_R, int(round(size * S)))

    def text(self, x, y, s, size, color, bold=True, track=0.0):
        f = self.font(size, bold)
        cx = self.s(x)
        for ch in s:
            self.d.text((cx, self.s(y)), ch, font=f, fill=rgba(color))
            cx += self.d.textlength(ch, font=f) + track * S
        return cx

    def width_of(self, s, size, bold=True, track=0.0):
        f = self.font(size, bold)
        return (self.d.textlength(s, font=f) + track * S * max(0, len(s) - 1)) / S

    def text_mid(self, cx, y, s, size, color, bold=True, track=0.0):
        self.text(cx - self.width_of(s, size, bold, track) / 2, y, s, size, color, bold, track)

    def text_end(self, rx, y, s, size, color, bold=True, track=0.0):
        self.text(rx - self.width_of(s, size, bold, track), y, s, size, color, bold, track)

    def finish(self):
        self.img.alpha_composite(self.glow.filter(ImageFilter.GaussianBlur(self.s(10))))
        self.img.alpha_composite(self.glow.filter(ImageFilter.GaussianBlur(self.s(2))))


# --------------------------------------------------------------------------- background
def build_bg(p):
    """The launcher's own wallpaper (BG10 Abyss Teal), only colour-graded per palette."""
    art = Image.open(WALL).convert("RGB")
    art = ImageOps.fit(art, (W * S, H * S), method=Image.LANCZOS)

    if p["wall_mix"] > 0:
        # Tint towards the palette accent, then blend back so the original composition and
        # light rays stay exactly where they are.
        grey = ImageOps.autocontrast(ImageOps.grayscale(art), cutoff=0)
        low = lerp(p["panel"], (0, 0, 0), 0.60)
        mid = lerp(p["panel"], p["cyan"], 0.38)
        high = lerp(p["cyan"], (255, 255, 255), 0.55)
        toned = ImageOps.colorize(grey, black=low, white=high, mid=mid)
        toned = ImageEnhance.Color(toned).enhance(1.05)
        art = Image.blend(art, toned, p["wall_mix"])

    art = ImageEnhance.Brightness(art).enhance(0.86)

    # bg_lucifer_scene: vertical #2E000000 -> #52000000 wash
    shade = Image.new("L", art.size, 0)
    sd = ImageDraw.Draw(shade)
    for y in range(art.size[1]):
        t = y / (art.size[1] - 1)
        sd.line([(0, y), (art.size[0], y)], fill=int(40 + t * 34))
    art = Image.composite(Image.new("RGB", art.size, (0, 0, 0)), art, shade)

    # very faint accent bloom behind the hero, matching bg_sd_shadow_flame_stage
    g = Image.new("RGBA", art.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.ellipse([art.size[0] * 0.40, art.size[1] * 0.26, art.size[0] * 0.60, art.size[1] * 0.92],
               fill=rgba(p["cyan"], 22))
    gd.ellipse([art.size[0] * 0.58, art.size[1] * 0.50, art.size[0] * 0.76, art.size[1] * 0.98],
               fill=rgba(p["magenta"], 18))
    g = g.filter(ImageFilter.GaussianBlur(art.size[0] // 20))
    return Image.alpha_composite(art.convert("RGBA"), g).convert("RGB")


# --------------------------------------------------------------------------- skin sprite
def skin_sprite(slim=False, scale=6):
    """Exact port of MinecraftSkinPreviewRenderer.renderFront (64x128 base sprite)."""
    atlas = Image.open(SKIN).convert("RGBA")
    modern = atlas.height >= 64
    arm_w = 3 if (modern and slim) else 4
    base = Image.new("RGBA", (16, 32), (0, 0, 0, 0))

    def part(src, dst, sw=4, sh=12, dx=0, dy=0, dw=None, dh=None, mirror=False):
        dw = sw if dw is None else dw
        dh = sh if dh is None else dh
        sxx, syy = src
        piece = atlas.crop((sxx, syy, sxx + sw, syy + sh))
        if mirror:
            piece = ImageOps.mirror(piece)
        base.alpha_composite(piece.resize((dw, dh), Image.NEAREST), (dst[0], dst[1]))

    # legs (behind)
    part((20, 52) if modern else (4, 20), (4, 20), 4, 12, mirror=not modern)
    part((4, 20), (8, 20), 4, 12)
    # arms
    legacy_arm_x = 44 + max(0, 4 - arm_w)
    part((36, 52) if modern else (legacy_arm_x, 20), (0, 8), arm_w, 12,
         dw=arm_w, dh=12, mirror=not modern)
    part((44, 20), (16 - arm_w, 8), arm_w, 12, dw=arm_w, dh=12)
    # torso + head
    part((20, 20), (4, 8), 8, 12)
    part((8, 8), (4, 0), 8, 8)
    # second layers
    if modern:
        part((4, 52), (4, 20))
        part((4, 36), (0, 8))
        part((52, 52), (16 - arm_w, 8), arm_w, 12, dw=arm_w, dh=12)
        part((44, 36), (0, 8), arm_w, 12, dw=arm_w, dh=12)
        part((20, 36), (4, 8), 8, 12)
    part((40, 8), (4, 0), 8, 8)  # hat layer
    return base.resize((16 * scale, 32 * scale), Image.NEAREST)


def draw_hero(sc, p, cx, base_y, height):
    """Full-body front view, same composition the app uses for the home avatar."""
    sprite = skin_sprite(scale=16)
    target_h = int(height * S)
    target_w = int(sprite.width * target_h / sprite.height)
    sprite = sprite.resize((target_w, target_h), Image.NEAREST)

    x = int(sc.s(cx) - target_w / 2)
    y = int(sc.s(base_y) - target_h)

    # soft contact shadow on the pedestal
    sh = Image.new("RGBA", (int(target_w * 0.85), max(8, target_h // 16)), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([0, 0, sh.width - 1, sh.height - 1], fill=(0, 0, 0, 135))
    sh = sh.filter(ImageFilter.GaussianBlur(target_h // 40))
    sc.img.alpha_composite(sh, (x + (target_w - sh.width) // 2, y + target_h - sh.height // 3))
    sc.redraw()

    # rim light so the sprite separates from the stage
    rim = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    alpha = sprite.split()[3]
    glow = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(7))
    tint = Image.new("RGBA", sprite.size, rgba(p["cyan"], 200))
    rim = Image.composite(tint, rim, glow)
    sc.img.alpha_composite(rim, (x, y))
    sc.redraw()

    sc.img.alpha_composite(sprite, (x, y))
    sc.redraw()


def draw_stage(sc, p, x, y, w, h):
    """bg_sd_shadow_flame_stage: soft aura, twin flame tongues, pedestal ring, spikes."""
    cx = x + w / 2
    ring_y = y + h * 0.86
    rx, ry = w * 0.42, h * 0.44

    # aura: soft radial wash, never a hard silhouette
    sc.halo(cx, y + h * 0.60, min(rx * 1.35, w * 0.52), p["cyan"], 26)
    sc.halo(cx, ring_y - h * 0.01, rx * 0.95, p["magenta"], 22)

    def P(px, py):
        return (cx + px * rx, ring_y + py * ry)

    # a soft ring of light instead of drawn flames: the app's vector flames read as
    # clutter behind a full-body skin at this size
    sc.halo(cx, ring_y - h * 0.22, w * 0.34, p["cyan"], 26)

    # pedestal platform: filled ellipse, lit rim, crystal shards at the edges
    plat_w = w * 0.62
    plat_h = max(16, h * 0.075)
    px0, py0 = cx - plat_w / 2, ring_y - plat_h / 2
    sc.halo(cx, ring_y, plat_w * 0.55, p["magenta"], 34)
    sc.ellipse(px0, py0, plat_w, plat_h,
               fill=rgba(lerp(p["panel"], p["cyan"], 0.22), 200),
               outline=rgba(p["cyan"], 255), width=1.6)
    sc.ellipse(px0 + plat_w * 0.10, py0 + plat_h * 0.18, plat_w * 0.80, plat_h * 0.62,
               fill=rgba(p["magenta"], 55))
    sc.ellipse(px0 + plat_w * 0.24, py0 + plat_h * 0.32, plat_w * 0.52, plat_h * 0.36,
               fill=rgba(p["cyan"], 70))
    for dx in (-0.52, 0.52):
        bx = cx + plat_w * dx
        sc.poly([(bx, ring_y + plat_h * 0.40), (bx + (8 if dx > 0 else -8), ring_y - plat_h * 0.85),
                 (bx + (16 if dx > 0 else -16), ring_y + plat_h * 0.42)],
                fill=rgba(p["cyan"] if dx < 0 else p["magenta"], 245))
    sc.flush_glow()


def draw_reactor(sc, p, x, y, w, h):
    """ic_sd_reactor_idle: crystal star + hexagonal plasma core + PLAY label."""
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w * 0.47, h * 0.44

    sc.halo(cx, cy, min(w, h) * 0.50, p["magenta"], 52)
    sc.flush_glow()

    outer, inner = [], []
    for i in range(20):
        a = math.radians(-90 + i * 18)
        rr = 1.0 if i % 2 == 0 else 0.80
        outer.append((cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr))
        inner.append((cx + math.cos(a) * rx * rr * 0.90, cy + math.sin(a) * ry * rr * 0.90))

    sc.poly(outer, fill=rgba(lerp(p["magenta"], (0, 0, 0), 0.28), 255))
    sc.poly(inner, fill=rgba(p["magenta"], 255))

    # facet highlights on the star points
    for i in range(0, 20, 2):
        tip = inner[i]
        left = inner[(i - 1) % 20]
        right = inner[(i + 1) % 20]
        sc.poly([tip, left, (cx, cy)], fill=rgba(lerp(p["magenta"], (255, 255, 255), 0.26), 150))
        sc.poly([tip, right, (cx, cy)], fill=rgba(lerp(p["magenta"], (0, 0, 0), 0.18), 130))
    for i in range(2, 20, 4):
        sc.poly([inner[i], inner[(i + 1) % 20], (cx, cy)], fill=rgba(p["cyan"], 95))

    hexa = [(cx - rx * 0.60, cy - ry * 0.44), (cx + rx * 0.60, cy - ry * 0.44),
            (cx + rx * 0.78, cy), (cx + rx * 0.60, cy + ry * 0.44),
            (cx - rx * 0.60, cy + ry * 0.44), (cx - rx * 0.78, cy)]
    sc.poly(hexa, fill=rgba(lerp(p["panel"], (0, 0, 0), 0.35), 250),
            outline=rgba(p["cyan"], 255), width=2.4)

    core = [(cx - rx * 0.52, cy - ry * 0.33), (cx + rx * 0.52, cy - ry * 0.33),
            (cx + rx * 0.68, cy), (cx + rx * 0.52, cy + ry * 0.33),
            (cx - rx * 0.52, cy + ry * 0.33), (cx - rx * 0.68, cy)]
    sc.poly(core, fill=rgba(lerp(p["magenta"], p["panel"], 0.80), 242),
            outline=rgba(lerp(p["magenta"], (255, 255, 255), 0.45), 210), width=1.3)
    sc.poly([(cx - rx * 0.50, cy - ry * 0.31), (cx + rx * 0.50, cy - ry * 0.31),
             (cx + rx * 0.52, cy - ry * 0.24), (cx - rx * 0.52, cy - ry * 0.24)],
            fill=rgba(p["cyan"], 30))

    bolt = [(cx + 1, cy - ry * 0.46), (cx + 9, cy - ry * 0.46), (cx + 5, cy - ry * 0.28),
            (cx + 10, cy - ry * 0.28), (cx - 2, cy - ry * 0.04), (cx + 1, cy - ry * 0.24),
            (cx - 4, cy - ry * 0.24)]
    sc.poly(bolt, fill=rgba(lerp(p["cyan"], (255, 255, 255), 0.60), 255))

    sc.text_mid(cx, cy + ry * 0.02, "PLAY", 24, (255, 255, 255), track=3.6)
    sc.text_mid(cx, cy + ry * 0.24, "SHADOW DRAGON READY", 6.8,
                lerp(p["cyan"], (255, 255, 255), 0.45), track=1.1)


# --------------------------------------------------------------------------- dock/header
def header(sc, p):
    top, hh = 16, 50
    sc.plate(20, top, 268, hh, p)
    em = Image.open(EMBLEM).convert("RGBA")
    eh = int((hh - 16) * S)
    em = em.resize((int(em.width * eh / em.height), eh), Image.LANCZOS)
    sc.img.alpha_composite(em, (sc.s(32), sc.s(top + 8)))
    sc.redraw()
    sc.text(66, top + 13, "LUCIFER", 21, (255, 255, 255), track=1.6)

    tel_w = 372
    sc.plate((W - tel_w) / 2, top + 4, tel_w, hh - 8, p, radius=9)
    tx = (W - tel_w) / 2 + 24
    tx = sc.text(tx, top + 17, "VULKAN 1.3", 11, p["cyan"], track=1.0) / S + 11
    tx = sc.text(tx, top + 16, "•", 12, (255, 255, 255)) / S + 11
    tx = sc.text(tx, top + 17, "144 FPS", 11, (255, 255, 255), track=1.0) / S + 11
    tx = sc.text(tx, top + 16, "•", 12, (255, 255, 255)) / S + 11
    sc.text(tx, top + 17, "6.0 GB RAM", 11, p["magenta"], track=1.0)

    # middle nav items (Scene, Cursor, About, PRO)
    labels = [("Scene", 0), ("Cursor", 1), ("About", 2)]
    nx = (W - tel_w) / 2 + tel_w + 34
    for label, _ in labels:
        pw = sc.width_of(label, 9, track=0.8) + 26
        sc.rect(nx, top + 12, pw, 30, fill=rgba(p["panel"], 210), radius=8,
                outline=rgba(p["cyan"], 90))
        sc.text_mid(nx + pw / 2, top + 22, label, 9, (255, 255, 255), track=0.8)
        nx += pw + 8

    acc_w = 210
    ax = W - 20 - acc_w
    sc.plate(ax, top, acc_w, hh, p)
    sc.text(ax + 16, top + 15, "SAIFKHAN", 11.5, (255, 255, 255), track=0.6)
    sc.text(ax + 16, top + 31, "LOCAL", 7, p["cyan"], track=1.2)
    # settings glyph
    gcx, gcy = ax + acc_w - 22, top + hh / 2
    for i in range(6):
        a = i * math.pi / 3
        sc.rect(gcx + math.cos(a) * 6 - 1.6, gcy + math.sin(a) * 6 - 1.6, 3.2, 3.2,
                fill=rgba(p["cyan"], 230), radius=1)
    sc.ellipse(gcx - 5, gcy - 5, 10, 10, fill=rgba(p["cyan"], 235))
    sc.ellipse(gcx - 2, gcy - 2, 4, 4, fill=rgba(p["panel"], 255))


def dock(sc, p):
    dh = 58
    dy = H - 16 - dh
    dw = 760
    dx = (W - dw) / 2
    pw, ph = sc.s(dw), sc.s(dh)
    g = vgrad((pw, ph), lerp(p["panel"], (0, 0, 0), 0.1), p["panel_hi"]).convert("RGBA")
    g.putalpha(rounded_mask((pw, ph), sc.s(14)).point(lambda v: int(v * 232 / 255)))
    sc.img.alpha_composite(g, (sc.s(dx), sc.s(dy)))
    sc.redraw()
    sc.d.rounded_rectangle(sc.box(dx, dy, dw, dh), sc.s(14), outline=rgba(p["cyan"], 175),
                           width=max(1, sc.s(1.5)))
    sc.d.rounded_rectangle(sc.box(dx + 2, dy + 2, dw - 4, dh - 4), sc.s(12),
                           outline=rgba(p["magenta"], 80), width=max(1, sc.s(1)))
    sc.soft_box(dx, dy, dw, dh, 14, p["cyan"], 45, 8)

    tabs = ["HOME", "PROFILES", "MODS", "SERVERS", "CONTROLS", "SKINS", "SETTINGS"]
    tw = dw / len(tabs)
    for i, label in enumerate(tabs):
        tcx = dx + tw * i + tw / 2
        active = i == 0
        col = p["cyan"] if active else (176, 190, 200)
        # small glyph above the label
        gy = dy + 19
        if label == "HOME":
            sc.poly([(tcx, gy - 6), (tcx + 7, gy + 1), (tcx + 4, gy + 1), (tcx + 4, gy + 7),
                     (tcx - 4, gy + 7), (tcx - 4, gy + 1), (tcx - 7, gy + 1)], fill=rgba(col))
        elif label == "PROFILES":
            sc.ellipse(tcx - 3, gy - 6, 6, 6, fill=rgba(col))
            sc.ellipse(tcx - 6, gy + 1, 12, 8, fill=rgba(col))
        elif label == "MODS":
            sc.poly([(tcx, gy - 6), (tcx + 6, gy - 3), (tcx, gy), (tcx - 6, gy - 3)], fill=rgba(col))
            sc.poly([(tcx - 6, gy - 3), (tcx, gy), (tcx, gy + 6), (tcx - 6, gy + 3)],
                    fill=rgba(lerp(col, (0, 0, 0), 0.3)))
            sc.poly([(tcx + 6, gy - 3), (tcx, gy), (tcx, gy + 6), (tcx + 6, gy + 3)],
                    fill=rgba(lerp(col, (0, 0, 0), 0.15)))
        elif label == "SERVERS":
            for dy2 in (-4, 1):
                sc.rect(tcx - 6, gy + dy2, 12, 4, fill=rgba(col), radius=1)
        elif label == "CONTROLS":
            sc.ellipse(tcx - 7, gy - 4, 14, 8, fill=rgba(col))
            sc.rect(tcx - 2, gy - 1, 4, 3, fill=rgba(p["panel"], 220))
        elif label == "SKINS":
            sc.rect(tcx - 6, gy - 6, 12, 11, fill=rgba(col), radius=1.5)
            sc.rect(tcx - 3, gy - 3, 2, 2, fill=rgba(p["panel"], 235))
            sc.rect(tcx + 1, gy - 3, 2, 2, fill=rgba(p["panel"], 235))
        else:
            sc.ellipse(tcx - 5, gy - 5, 10, 10, fill=rgba(col))
            sc.ellipse(tcx - 2, gy - 2, 4, 4, fill=rgba(p["panel"], 235))

        sc.text_mid(tcx, dy + 34, label, 8.5, (255, 255, 255) if active else (168, 182, 194),
                    track=0.9)
        if active:
            sc.rect(tcx - 22, dy + dh - 8, 44, 2.6, fill=rgba(p["cyan"], 255), radius=1.5)

    # crystal end caps
    for side, ex in ((-1, dx), (1, dx + dw)):
        sc.poly([(ex, dy + 12), (ex + side * 13, dy + dh / 2), (ex, dy + dh - 12),
                 (ex - side * 6, dy + dh / 2)],
                fill=rgba(lerp(p["cyan"], p["panel"], 0.55), 235), outline=rgba(p["magenta"], 200),
                width=1.2)


# --------------------------------------------------------------------------- composition
def render(p):
    sc = Screen(build_bg(p))
    header(sc, p)

    stage_top = 84
    dock_top = H - 16 - 58
    content_bottom = dock_top - 16
    content_h = content_bottom - stage_top

    # ---- left column (41% guideline)
    lx, lw = 20, int(W * 0.41) - 24
    srv_h = 128
    sc.card(lx, stage_top, lw, srv_h, p, glow=True)
    sc.text(lx + 16, stage_top + 13, "LUCIFERMC — LIFESTEEL SMP", 11.5, (255, 255, 255), track=0.5)
    bw = sc.width_of("OFFICIAL", 7.5, track=0.8) + 16
    sc.grad_rect(lx + lw - 16 - bw, stage_top + 12, bw, 17, lerp(p["magenta"], (0, 0, 0), 0.15),
                 p["magenta"], radius=5)
    sc.text_mid(lx + lw - 16 - bw / 2, stage_top + 16, "OFFICIAL", 7.5, (10, 10, 14), track=0.8)
    sc.text(lx + 16, stage_top + 38, "play.lucifermc.fun", 10, p["cyan"], bold=False)
    sc.text_end(lx + lw - 16, stage_top + 38, "● LIVE · 24ms", 9, (52, 211, 153), track=0.4)

    by = stage_top + srv_h - 38
    join_w = 128
    sc.grad_rect(lx + 16, by, join_w, 24, lerp(p["cyan"], (255, 255, 255), 0.28), p["cyan"], radius=7)
    sc.text_mid(lx + 16 + join_w / 2, by + 7, "JOIN", 9.5, (4, 8, 18), track=1.8)
    rest = lw - 32 - join_w - 10
    for i, label in enumerate(("DISCORD", "WIKI")):
        pw = rest / 2 - 5
        px = lx + 16 + join_w + 10 + i * (pw + 10)
        sc.rect(px, by, pw, 24, fill=rgba(lerp(p["panel"], p["magenta"], 0.10), 235), radius=7,
                outline=rgba(p["cyan"], 120))
        sc.text_mid(px + pw / 2, by + 7.5, label, 8, (255, 255, 255), track=0.9)

    # active build card
    ab_y = stage_top + srv_h + 12
    ab_h = content_bottom - ab_y
    sc.card(lx, ab_y, lw, ab_h, p)
    sc.text(lx + 16, ab_y + 13, "ACTIVE BUILD // VERSION", 7.5, p["magenta"], track=1.6)
    sc.text(lx + 16, ab_y + 27, "Fabric 1.21.4 — Shadow PvP", 15.5, (255, 255, 255), track=0.3)
    sc.text(lx + 16, ab_y + 50, "Fabric Loader 0.16 • Sodium + Iris • 6.0 GB RAM", 9, p["cyan"],
            bold=False)

    # build detail rows (what the instance card shows in the app)
    details = [("VERSION", "1.21.10"), ("LOADER", "Fabric 0.16.9"),
               ("MODS", "42 active"), ("SHADER", "Complementary"),
               ("MEMORY", "6.0 GB"), ("STATUS", "Ready to launch")]
    ry0 = ab_y + 74
    row_h = 27
    for i, (k, v) in enumerate(details):
        yy = ry0 + i * row_h
        sc.rect(lx + 16, yy, lw - 32, 22,
                fill=rgba(lerp(p["panel"], p["cyan"], 0.05), 165), radius=6,
                outline=rgba(p["cyan"], 45))
        sc.text(lx + 27, yy + 7, k, 7, p["magenta"], track=1.2)
        sc.text_end(lx + lw - 27, yy + 6.5, v, 8, (255, 255, 255), track=0.3)

    # top mods strip
    mods = ["Sodium", "Iris", "Lithium", "Krypton", "Ferrite"]
    mx = lx + 16
    my = ry0 + len(details) * row_h + 14
    sc.text(mx, my, "TOP MODS", 7, p["magenta"], track=1.4)
    mx_y = my + 16
    for name in mods:
        pw = sc.width_of(name, 7.5, track=0.4) + 18
        sc.rect(mx, mx_y, pw, 19, fill=rgba(lerp(p["panel"], p["cyan"], 0.12), 200), radius=6,
                outline=rgba(p["cyan"], 90))
        sc.text_mid(mx + pw / 2, mx_y + 5.5, name, 7.5, (255, 255, 255), track=0.4)
        mx += pw + 7

    # recent instances
    rec_y = mx_y + 46
    sc.text(lx + 16, rec_y, "RECENT INSTANCES", 7, p["magenta"], track=1.4)
    recents = [("Lifesteel SMP", "1.21.10 · 2 days ago"), ("Skyblock Legends", "1.20.6 · 5 days ago")]
    for i, (name, meta) in enumerate(recents):
        ry = rec_y + 18 + i * 34
        sc.rect(lx + 16, ry, lw - 32, 30, fill=rgba(lerp(p["panel"], (0, 0, 0), 0.18), 190),
                radius=7, outline=rgba(p["cyan"], 55))
        icx, icy = lx + 34, ry + 15
        sc.poly([(icx, icy - 7), (icx + 8, icy - 3), (icx, icy + 1), (icx - 8, icy - 3)],
                fill=rgba(p["cyan"], 230))
        sc.poly([(icx - 8, icy - 3), (icx, icy + 1), (icx, icy + 7), (icx - 8, icy + 3)],
                fill=rgba(lerp(p["cyan"], (0, 0, 0), 0.35), 230))
        sc.poly([(icx + 8, icy - 3), (icx, icy + 1), (icx, icy + 7), (icx + 8, icy + 3)],
                fill=rgba(lerp(p["cyan"], (0, 0, 0), 0.18), 230))
        sc.text(lx + 50, ry + 6, name, 8.5, (255, 255, 255), track=0.3)
        sc.text(lx + 50, ry + 18, meta, 7, p["cyan"], bold=False)

    # action row
    arow_y = ab_y + ab_h - 96
    acts = [("MODS DIR", 1.25), ("+ NEW", 1.0), ("RELOAD", 0.62)]
    total_w = lw - 32
    used = sum(w for _, w in acts)
    ax = lx + 16
    for label, weight in acts:
        pw = total_w * weight / used - 6
        solid = label.startswith("+")
        if solid:
            sc.grad_rect(ax, arow_y, pw, 22, lerp(p["magenta"], p["cyan"], 0.25),
                         lerp(p["magenta"], (0, 0, 0), 0.2), radius=6)
        else:
            sc.rect(ax, arow_y, pw, 22, fill=rgba(p["panel"], 225), radius=6,
                    outline=rgba(p["cyan"], 95))
        sc.text_mid(ax + pw / 2, arow_y + 6.5, label, 7.5,
                    (255, 255, 255) if solid else p["cyan"], track=0.8)
        ax += pw + 6

    # quick-switch profile strip
    chips = [("Fabric 1.21.10", "Mods: 42 · Ready", True),
             ("LuciferMC SMP", "Mods: 28 · Official", False),
             ("CS Client", "Mods: 0 · Clean", False),
             ("+ New Instance", "Create profile", False)]
    gap = 8
    chip_w = (total_w - gap * 3) / 4
    chip_y = arow_y + 30
    chip_h = ab_h - (chip_y - ab_y) - 14
    for i, (title, sub, sel) in enumerate(chips):
        cx0 = lx + 16 + i * (chip_w + gap)
        if sel:
            sc.grad_rect(cx0, chip_y, chip_w, chip_h,
                         lerp(p["magenta"], p["panel"], 0.62),
                         lerp(p["cyan"], p["panel"], 0.70), radius=9)
            sc.d.rounded_rectangle(sc.box(cx0, chip_y, chip_w, chip_h), sc.s(9),
                                   outline=rgba(p["cyan"], 220), width=max(1, sc.s(1.4)))
        else:
            sc.rect(cx0, chip_y, chip_w, chip_h, fill=rgba(lerp(p["panel"], (0, 0, 0), 0.15), 220),
                    radius=9, outline=rgba(p["magenta"], 70))
        sc.text(cx0 + 9, chip_y + 8, title, 8.5, (255, 255, 255), track=0.2)
        sc.text(cx0 + 9, chip_y + 23, sub, 7, p["cyan"] if sel else (150, 164, 176), bold=False)

    # ---- center hero stage (41% .. 69%)
    c_x = int(W * 0.41) + 6
    c_w = int(W * 0.69) - c_x - 6
    draw_stage(sc, p, c_x, stage_top, c_w, content_h)
    draw_hero(sc, p, c_x + c_w / 2, stage_top + content_h * 0.879, int(content_h * 0.63))

    pill_w = 118
    sc.plate(c_x + c_w / 2 - pill_w / 2, content_bottom - 26, pill_w, 22, p, radius=7)
    sc.text_mid(c_x + c_w / 2, content_bottom - 21, "SKIN STUDIO", 7.5, p["cyan"], track=1.2)

    # ---- right column (69% .. 100%)
    rx = int(W * 0.69) + 8
    rw = W - 20 - rx
    ar_h = 84
    sc.card(rx, stage_top, rw, ar_h, p, glow=True)
    sc.text(rx + 14, stage_top + 12, "SHADOW DRAGON ARSENAL", 7.5, p["cyan"], track=1.4)
    pw = (rw - 28 - 8) / 2
    for i, label in enumerate(("MOD STORE", "HUD KEYS")):
        px = rx + 14 + i * (pw + 8)
        sc.rect(px, stage_top + 30, pw, 26, fill=rgba(lerp(p["panel"], p["magenta"], 0.12), 232),
                radius=7, outline=rgba(p["cyan"], 110))
        sc.text_mid(px + pw / 2, stage_top + 39, label, 7.5,
                    (255, 255, 255) if i == 0 else p["magenta"], track=0.6)

    r_y = stage_top + ar_h + 12
    r_h = content_bottom - r_y
    draw_reactor(sc, p, rx, r_y, rw, r_h)

    dock(sc, p)
    sc.finish()

    out = sc.img.convert("RGB").resize((W, H), Image.LANCZOS)
    path = OUT / f"{p['slug']}.png"
    out.save(path, "PNG", optimize=True)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) or None
    for p in PALETTES:
        if only and p["slug"] not in only:
            continue
        print("wrote", render(p).relative_to(ROOT))


if __name__ == "__main__":
    main()
