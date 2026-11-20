"""Pixel-size-1 world art for HumanLang Odyssey, drawn with shading and ordered dithering (no outside pictures).

Everything is made of a few ramps of colours (dark to light) and a shape mask. `shade` lights a mask from the top left,
`outline` draws the dark one-pixel edge, and the results are RGBA pictures that pixelkit turns into sprite rows.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
INK = (15, 18, 36)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


RAMPS = {
    "grass": ["#173d27", "#24663a", "#3b8f43", "#63b84a", "#97df63", "#d4f58f"],
    "leaf": ["#12372a", "#1c5a35", "#2b8240", "#45aa4a", "#7ad161", "#b9f08a"],
    "pine": ["#0f2c33", "#164a45", "#1f6b52", "#2f8c5d", "#52b274", "#8bd698"],
    "dirt": ["#2b1b14", "#47291c", "#663b25", "#865135", "#a96d45", "#cb9162"],
    "stone": ["#1c2036", "#303659", "#4b5380", "#6b75a8", "#929bcb", "#c1c8ea"],
    "wood": ["#2a1810", "#4a2a18", "#6d4024", "#93602f", "#b98242", "#e0aa66"],
    "snow": ["#5b6ea6", "#8a9cd0", "#b9c8ee", "#dce6fb", "#f6f9ff"],
    "cloud": ["#7f93c7", "#a9bbe6", "#cfdbf6", "#eef3ff", "#ffffff"],
    "rock": ["#23263a", "#3b4060", "#5a6285", "#7f88ae", "#a7b0d3"],
    "metal": ["#1b2033", "#2f3a58", "#4a5a82", "#7289b8", "#a9c0e8", "#e1ecff"],
    "gold": ["#5a3a08", "#8c5c0e", "#c48a1a", "#f0b832", "#ffd95c", "#fff2b0"],
    "blue": ["#0b2a5a", "#0f4a95", "#1480d6", "#2eb2f5", "#7fd6ff", "#dcf4ff"],
    "purple": ["#22104a", "#3d1c86", "#5f2fc4", "#8a52ee", "#b78aff", "#e2ccff"],
    "red": ["#4a0c18", "#7d1426", "#b81e34", "#e43a4c", "#ff7f86", "#ffc9c9"],
    "orange": ["#5a2208", "#923b0e", "#d26414", "#f9902a", "#ffb85e", "#ffe0a8"],
    "green": ["#0b3a24", "#106a3c", "#18a355", "#3fd477", "#8ff2ae", "#d2ffe0"],
    "pink": ["#4a0f3a", "#841a63", "#c52a94", "#ef55c0", "#ff94dd", "#ffd1f0"],
    "bug": ["#1a0f33", "#3a1a6b", "#6a2fb8", "#9a56e6", "#c58cff", "#ecd2ff"],
}


def ramp(name):
    return [rgb(c) for c in RAMPS[name]]


def cols_of(x):
    """A ramp by name, or a list of colours given as '#rrggbb' text or (r, g, b)."""
    if isinstance(x, str):
        return ramp(x)
    return [rgb(c) if isinstance(c, str) else tuple(c) for c in x]


class Pic:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), dtype="uint8")
        self.yy, self.xx = np.mgrid[0:h, 0:w]

    # ---- masks -------------------------------------------------------------------
    def ellipse(self, cx, cy, rx, ry):
        return ((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2 <= 1.0

    def poly(self, pts):
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
        return np.array(im) > 0

    def rect(self, x0, y0, x1, y1):
        return (self.xx >= x0) & (self.xx < x1) & (self.yy >= y0) & (self.yy < y1)

    # ---- painting ----------------------------------------------------------------
    def fill(self, mask, colour):
        self.a[mask] = (*colour, 255)

    def shade(self, mask, rampname, light=(-0.6, -0.8), roughness=0.0, seed=1, bias=0.0, top=None, bottom=None):
        """Light a shape from the top left, with ordered dithering between the ramp colours."""
        cols = cols_of(rampname)
        n = len(cols)
        if not mask.any():
            return
        d = ndimage.distance_transform_edt(mask)
        dm = max(d.max(), 1)
        ys, xs = np.nonzero(mask)
        cx, cy = xs.mean(), ys.mean()
        rx, ry = max(xs.max() - xs.min(), 1) / 2, max(ys.max() - ys.min(), 1) / 2
        nx, ny = (self.xx - cx) / rx, (self.yy - cy) / ry
        lit = -(nx * light[0] + ny * light[1])                 # 1 facing the light, -1 away
        t = 0.52 + 0.30 * np.clip(lit, -1.2, 1.2) + 0.28 * np.minimum(d / (0.6 * dm), 1.0) - 0.14 + bias
        if roughness:
            rng = np.random.default_rng(seed)
            noise = ndimage.gaussian_filter(rng.random((self.h, self.w)), 0.8)
            t += roughness * (noise - noise.mean()) * 4
        t = np.clip(t, 0, 0.999)
        lo = (top, bottom)
        v = t * (n - 1)
        base = np.floor(v)
        idx = np.clip(base + (v - base > BAYER[self.yy % 4, self.xx % 4]), 0, n - 1).astype(int)
        arr = np.array(cols, dtype="uint8")[idx]
        self.a[mask, :3] = arr[mask]
        self.a[mask, 3] = 255

    def vgrad(self, mask, rampname, y0, y1, dither=True, flip=False):
        cols = cols_of(rampname)
        n = len(cols)
        t = np.clip((self.yy - y0) / max(y1 - y0, 1), 0, 0.999)
        if flip:
            t = 1 - t
        v = t * (n - 1)
        base = np.floor(v)
        idx = np.clip(base + ((v - base) > BAYER[self.yy % 4, self.xx % 4] if dither else 0), 0, n - 1).astype(int)
        arr = np.array(cols, dtype="uint8")[idx]
        self.a[mask, :3] = arr[mask]
        self.a[mask, 3] = 255

    def speckle(self, mask, colour, chance, seed=3):
        rng = np.random.default_rng(seed)
        hit = mask & (rng.random((self.h, self.w)) < chance) & (self.a[..., 3] > 0)
        self.a[hit] = (*colour, 255)

    def line(self, pts, colour, width=1):
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).line([tuple(p) for p in pts], fill=255, width=width)
        m = np.array(im) > 0
        self.a[m] = (*colour, 255)

    def outline(self, colour=INK, inner=False):
        solid = self.a[..., 3] > 0
        edge = ndimage.binary_dilation(solid, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~solid
        self.a[edge] = (*colour, 255)

    def paste(self, other, x, y):
        im = self.image()
        im.alpha_composite(other.image() if isinstance(other, Pic) else other, (x, y))
        self.a = np.array(im)

    def image(self):
        return Image.fromarray(self.a.copy())


def blank(w, h):
    return Pic(w, h)


# =============================================================================================================
# tiles (16 x 16)
# =============================================================================================================
def tile_dirt(seed=1, deep=False):
    p = Pic(16, 16)
    m = np.ones((16, 16), bool)
    p.shade(m, "dirt", light=(0, -1), roughness=0.10, seed=seed, bias=-0.20 if deep else 0.02)
    rng = random.Random(seed)
    for _ in range(5):
        x, y = rng.randrange(1, 14), rng.randrange(2, 14)
        p.fill(p.rect(x, y, x + 2, y + 1), ramp("dirt")[1 if deep else 4])
        p.fill(p.rect(x, y + 1, x + 2, y + 2), ramp("dirt")[0])
    for _ in range(3):                                      # little stones
        x, y = rng.randrange(1, 12), rng.randrange(3, 13)
        p.fill(p.rect(x, y, x + 3, y + 2), ramp("rock")[2])
        p.fill(p.rect(x, y, x + 2, y + 1), ramp("rock")[4])
        p.fill(p.rect(x + 2, y + 1, x + 3, y + 2), ramp("rock")[0])
    return p


def tile_grass(seed=2):
    p = tile_dirt(seed)
    g = ramp("grass")
    top = np.zeros((16, 16), bool)
    top[0:5, :] = True
    rng = random.Random(seed)
    # the grass edge hangs down in blades of different length
    for x in range(16):
        top[5, x] = rng.random() < 0.7
        if rng.random() < 0.35:
            top[6, x] = True
    p.shade(top, "grass", light=(-0.3, -1), roughness=0.16, seed=seed + 5, bias=0.05)
    p.vgrad(p.rect(0, 0, 16, 2), [g[4], g[5]], 0, 2, dither=True)
    p.fill(p.rect(0, 0, 16, 1), g[5])
    for x in range(0, 16, 3):                                # blade tips
        p.fill(p.rect(x, 0, x + 1, 1), g[5])
    p.fill((p.yy == 4) & top & (p.xx % 2 == 0), g[1])
    p.fill((p.yy == 5) & top, g[0])
    p.fill((p.yy == 6) & top, g[0])
    return p


def tile_stone(seed=4, snow=False):
    p = Pic(16, 16)
    m = np.ones((16, 16), bool)
    p.shade(m, "stone", light=(-0.5, -0.9), roughness=0.08, seed=seed, bias=0.0)
    # brick joints
    j = ramp("stone")[0]
    for y in (0, 8):
        p.fill(p.rect(0, y, 16, y + 1), j)
    for x, (y0, y1) in ((7, (0, 8)), (2, (8, 16)), (12, (8, 16))):
        p.fill(p.rect(x, y0, x + 1, y1), j)
    for y, xs in ((1, (0, 8)), (9, (3, 13))):                # a light edge under every joint
        for x in range(16):
            if x not in xs:
                p.fill(p.rect(x, y, x + 1, y + 1), ramp("stone")[4])
    rng = random.Random(seed)
    for _ in range(6):
        x, y = rng.randrange(0, 15), rng.randrange(0, 15)
        p.fill(p.rect(x, y, x + 1, y + 1), ramp("stone")[1])
    if snow:
        s = ramp("snow")
        m2 = np.zeros((16, 16), bool)
        m2[0:4, :] = True
        for x in range(16):
            m2[4, x] = rng.random() < 0.6
        p.shade(m2, "snow", light=(-0.3, -1), roughness=0.05, seed=seed, bias=0.12)
        p.fill(p.rect(0, 0, 16, 1), s[4])
    return p


def tile_plank(seed=5):
    """A wooden bridge plank: the top 7 rows, the rest is air."""
    p = Pic(16, 16)
    m = np.zeros((16, 16), bool)
    m[0:7, :] = True
    p.shade(m, "wood", light=(-0.2, -1), roughness=0.05, seed=seed, bias=0.05)
    w = ramp("wood")
    p.fill(p.rect(0, 0, 16, 1), w[5])
    p.fill(p.rect(0, 6, 16, 7), w[0])
    p.fill(p.rect(7, 1, 8, 6), w[1])
    for x, y in ((3, 3), (12, 3)):
        p.fill(p.rect(x, y, x + 2, y + 2), w[0])
        p.fill(p.rect(x, y, x + 1, y + 1), w[5])
    p.fill(p.rect(0, 7, 16, 8), (0, 0, 0))                   # clear: planks have no base
    p.a[7:, :, 3] = 0
    return p


def tile_spike(seed=6):
    p = Pic(16, 16)
    m = ramp("metal")
    for x0, tip, wd in ((0, 5, 5), (5, 1, 6), (11, 5, 5)):
        tri = p.poly([(x0 + wd / 2.0, tip), (x0, 15.5), (x0 + wd, 15.5)])
        left = tri & (p.xx < x0 + wd / 2.0)
        right = tri & (p.xx >= x0 + wd / 2.0)
        p.fill(left, m[4])
        p.fill(right, m[2])
        p.fill(tri & (p.xx == int(x0 + wd / 2.0 - 1)) & (p.yy > tip + 1), m[5])
        p.fill(tri & (p.yy > 12), m[1])
    p.fill(p.rect(0, 15, 16, 16), m[0])
    p.outline(INK)
    return p


def tile_circuit(seed=7, glow="blue"):
    p = Pic(16, 16)
    m = np.ones((16, 16), bool)
    p.shade(m, ["#0a0e22", "#10183a", "#17235a", "#1d2f78"], light=(0, -1), roughness=0.03, seed=seed, bias=-0.1)
    c = ramp(glow)
    rng = random.Random(seed)
    p.fill(p.rect(0, 0, 16, 1), (46, 64, 130))
    p.fill(p.rect(0, 15, 16, 16), (5, 7, 18))
    # a copper-coloured trace with a glowing node
    y = 6
    p.fill(p.rect(2, y, 14, y + 1), c[2])
    p.fill(p.rect(2, y + 1, 14, y + 2), c[0])
    p.fill(p.rect(8, y + 1, 9, 13), c[2])
    p.fill(p.rect(7, 12, 10, 15), c[3])
    p.fill(p.rect(8, 13, 9, 14), c[5])
    p.fill(p.rect(2, 4, 4, 8), c[3])
    p.fill(p.rect(2, 4, 3, 5), c[5])
    return p


# =============================================================================================================
# scenery
# =============================================================================================================
def tree(w=60, h=76, seed=8):
    p = Pic(w, h)
    cx = w // 2
    # trunk with bark
    trunk = p.rect(cx - 5, h - 34, cx + 5, h) | p.poly([(cx - 5, h - 8), (cx - 10, h), (cx + 10, h), (cx + 5, h - 8)])
    p.shade(trunk, "wood", light=(-1, 0), roughness=0.12, seed=seed)
    for y in range(h - 32, h - 6, 4):
        p.fill(p.rect(cx - 3, y, cx - 1, y + 2), ramp("wood")[1])
        p.fill(p.rect(cx + 1, y + 2, cx + 3, y + 4), ramp("wood")[1])
    p.outline(INK)
    can = np.zeros((h, w), bool)
    for (x, y, rx, ry) in ((cx, 22, 24, 20), (cx - 15, 33, 15, 13), (cx + 15, 33, 15, 13), (cx, 38, 18, 12), (cx - 9, 14, 13, 11), (cx + 10, 15, 13, 11)):
        can |= p.ellipse(x, y, rx, ry)
    p.a[can] = 0
    p.shade(can, "leaf", light=(-0.7, -0.9), roughness=0.22, seed=seed + 1, bias=0.02)
    rng = random.Random(seed)
    leaf = ramp("leaf")
    for _ in range(70):                                       # leaf clumps: a light top and a dark underside
        x, y = rng.randrange(cx - 26, cx + 26), rng.randrange(5, 48)
        if p.a[y, x, 3] and 0 < x < w - 2:
            p.fill(p.rect(x, y, x + 3, y + 1), leaf[5 if y < 24 else 3])
            p.fill(p.rect(x, y + 1, x + 3, y + 2), leaf[1])
    for (x, y) in ((cx - 12, 22), (cx + 8, 28), (cx - 2, 36)):  # apples
        p.fill(p.ellipse(x, y, 2, 2), ramp("red")[3])
        p.fill(p.rect(x - 1, y - 1, x, y), ramp("red")[5])
    # canopy outline
    solid = p.a[..., 3] > 0
    edge = ndimage.binary_dilation(solid, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~solid
    p.a[edge] = (*INK, 255)
    return p


def pine(w=40, h=72, seed=9):
    p = Pic(w, h)
    cx = w // 2
    trunk = p.rect(cx - 3, h - 14, cx + 3, h)
    p.shade(trunk, "wood", light=(-1, 0), roughness=0.1, seed=seed)
    p.outline(INK)
    tiers = [(h - 56, 12), (h - 44, 16), (h - 31, 19), (h - 18, 22)]
    for i, (y, half) in enumerate(tiers):
        m = p.poly([(cx, y - 14), (cx - half, y + 10), (cx + half, y + 10)])
        m &= ~p.rect(0, h - 12, w, h)
        p.shade(m, "pine", light=(-0.9, -0.3), roughness=0.14, seed=seed + i, bias=0.02)
        p.fill(p.rect(cx - half + 1, y + 9, cx + half, y + 10), ramp("pine")[0])
        # a cap of snow on the two top tiers
        if i < 3:
            s = p.poly([(cx, y - 14), (cx - half // 2, y - 4), (cx + half // 2, y - 4)])
            p.shade(s, "snow", light=(-0.5, -1), bias=0.1)
    solid = p.a[..., 3] > 0
    edge = ndimage.binary_dilation(solid, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~solid
    p.a[edge] = (*INK, 255)
    return p


def bush(w=30, h=20, seed=10):
    p = Pic(w, h)
    m = p.ellipse(9, 12, 9, 7) | p.ellipse(17, 10, 10, 9) | p.ellipse(23, 13, 7, 6)
    m &= ~p.rect(0, h - 2, w, h)
    p.shade(m, "leaf", light=(-0.7, -0.9), roughness=0.22, seed=seed)
    rng = random.Random(seed)
    for _ in range(14):
        x, y = rng.randrange(3, w - 4), rng.randrange(3, h - 4)
        if p.a[y, x, 3]:
            p.fill(p.rect(x, y, x + 2, y + 1), ramp("leaf")[5])
    for (x, y) in ((7, 11), (19, 8), (24, 12)):
        p.fill(p.rect(x, y, x + 2, y + 2), ramp("pink")[4])
        p.fill(p.rect(x, y, x + 1, y + 1), ramp("pink")[5])
    p.outline(INK)
    return p


def flower(colour="pink", w=11, h=16, seed=11):
    p = Pic(w, h)
    c = ramp(colour)
    p.fill(p.rect(5, 7, 6, h), ramp("grass")[2])
    p.fill(p.rect(6, 10, 8, 11), ramp("grass")[3])
    p.fill(p.rect(3, 12, 5, 13), ramp("grass")[3])
    for dx, dy in ((0, -3), (-3, 0), (3, 0), (0, 3)):
        p.fill(p.ellipse(5 + dx, 4 + dy, 2.2, 2.2), c[3])
    for dx, dy in ((-1, -4), (-4, -1)):
        p.fill(p.rect(5 + dx, 4 + dy, 6 + dx, 5 + dy), c[5])
    p.fill(p.ellipse(5, 4, 1.6, 1.6), ramp("gold")[4])
    p.outline(INK)
    return p


def tuft(w=12, h=10, seed=12):
    p = Pic(w, h)
    g = ramp("grass")
    for i, (x, hh) in enumerate(((1, 5), (3, 8), (5, 6), (7, 9), (9, 5))):
        p.fill(p.rect(x, h - hh, x + 2, h), g[2 + (i % 2)])
        p.fill(p.rect(x, h - hh, x + 1, h), g[4])
    p.outline(INK)
    return p


def rock(w=26, h=16, seed=13):
    p = Pic(w, h)
    m = p.ellipse(13, 11, 12, 6) | p.ellipse(10, 8, 8, 6) | p.ellipse(18, 9, 7, 5)
    m &= ~p.rect(0, h - 1, w, h)
    p.shade(m, "rock", light=(-0.7, -0.8), roughness=0.2, seed=seed)
    p.line([(8, 5), (11, 9), (10, 12)], ramp("rock")[0])
    p.outline(INK)
    return p


def cloud(w, h, seed):
    p = Pic(w, h)
    rng = random.Random(seed)
    m = np.zeros((h, w), bool)
    base = h - 6
    n = max(3, w // 14)
    for i in range(n):
        x = int((i + 0.5) * w / n)
        r = rng.randint(max(4, h // 4), h // 2 - 1) + (3 if 0 < i < n - 1 else 0)
        m |= p.ellipse(x, base - r + 2, r + 3, r)
    m |= p.rect(6, base - 4, w - 6, base + 2)
    m &= ~p.rect(0, base + 2, w, h)
    p.shade(m, ["#8fa5dc", "#b5c6ee", "#d6e1f8", "#f0f5ff", "#ffffff"], light=(-0.3, -1), roughness=0.04, seed=seed, bias=0.02)
    # a flat, shaded underside
    under = m & (p.yy >= base - 1)
    p.shade(under, ["#7e93cc", "#9fb3e4", "#c0cff0"], light=(0, -1), bias=0.0)
    return p


def mountains(w=220, h=110, seed=14, palette="stone", snow=True, peaks=3):
    """A ridge of peaks, lit from the left: faces with gullies, snow on top, and a hazy foot that fades into the sky."""
    p = Pic(w, h)
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    xs = np.arange(w)
    ridge = np.zeros(w)
    owner = np.zeros(w, dtype=int)
    centres = []
    for i in range(peaks):
        cxm = w * (i + 0.6) / (peaks + 0.4) + rng.randint(-8, 8)
        hm = rng.randint(int(h * 0.62), int(h * 0.95))
        centres.append((cxm, hm, rng.uniform(0.8, 1.2)))
    for k, (cxm, hm, sl) in enumerate(centres):
        v = np.clip(hm - np.abs(xs - cxm) * sl, 0, None)
        owner = np.where(v > ridge, k, owner)
        ridge = np.maximum(ridge, v)
    jag = ndimage.gaussian_filter(nrng.random(w), 1.3) * 10
    ridge = np.clip(ridge + jag - 5, 0, h - 1)
    top = (h - ridge).astype(int)
    cols = ramp(palette)
    n = len(cols)
    gull = ndimage.gaussian_filter(nrng.random((h, w)), (2.5, 0.9))
    for x in range(w):
        cxm, hm, sl = centres[owner[x]]
        side = np.clip((x - cxm) / 38.0, -1, 1)                 # -1 far left (lit) ... +1 far right (shadow)
        for y in range(top[x], h):
            depth = (y - top[x]) / float(h)
            t = 0.74 - 0.42 * side + 0.6 * (gull[y, x] - 0.5) - 0.28 * depth + 0.10 * np.sin((x - y * 0.55) * 0.42)
            t = float(np.clip(t, 0, 0.999))
            vv = t * (n - 1)
            b = int(vv)
            idx = min(b + (1 if (vv - b) > BAYER[y % 4, x % 4] else 0), n - 1)
            p.a[y, x] = (*cols[idx], 255)
    if snow:
        sn = ramp("snow")
        for x in range(w):
            if ridge[x] > h * 0.5:
                cxm, hm, sl = centres[owner[x]]
                depth = int((ridge[x] - h * 0.5) * 0.5) + 2 + (x * 5 % 4)
                lit = -np.clip((x - cxm) / 38.0, -1, 1)
                for y in range(top[x], min(top[x] + depth, h)):
                    t = 0.55 + 0.4 * lit + 0.1 * np.sin(y * 0.9 + x * 0.4)
                    vv = float(np.clip(t, 0, 0.999)) * (len(sn) - 1)
                    b = int(vv)
                    idx = min(b + (1 if (vv - b) > BAYER[y % 4, x % 4] else 0), len(sn) - 1)
                    p.a[y, x] = (*sn[idx], 255)
    # outline the ridge
    solid = p.a[..., 3] > 0
    edge = ndimage.binary_dilation(solid, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]]) & ~solid
    p.a[edge] = (*[max(0, c - 40) for c in cols[0]], 255)
    # haze: the lowest part fades out with dithering, so the sky and the hills show through
    for y in range(int(h * 0.62), h):
        keep = 1.0 - (y - h * 0.62) / (h * 0.38)
        for x in range(w):
            if BAYER[y % 4, x % 4] > keep:
                p.a[y, x] = (0, 0, 0, 0)
    return p


def hills(w=220, h=56, seed=15):
    p = Pic(w, h)
    rng = random.Random(seed)
    xs = np.arange(w)
    ridge = h * 0.45 + 9 * np.sin(xs / 17.0 + rng.random() * 6) + 6 * np.sin(xs / 7.0 + rng.random() * 6)
    m = np.zeros((h, w), bool)
    for x in range(w):
        m[int(h - ridge[x] * 0.9 - 6):, x] = True
    p.shade(m, ["#1b4d3a", "#23674a", "#2f8558", "#44a468"], light=(-0.3, -1), roughness=0.12, seed=seed, bias=-0.05)
    return p


# =============================================================================================================
# things you meet
# =============================================================================================================
def coin(frame, w=14, h=14):
    p = Pic(w, h)
    rx = [6, 5, 3, 1.4][frame]
    m = p.ellipse(7, 7, rx, 6.5)
    p.shade(m, "gold", light=(-0.7, -0.7), bias=0.1)
    if rx > 3:
        inner = p.ellipse(7, 7, rx - 2.2, 4.4)
        p.fill(inner, ramp("gold")[2])
        p.fill(p.rect(6, 4, 8, 10), ramp("gold")[5] if frame == 0 else ramp("gold")[4])
    p.outline(INK)
    return p


def heart(w=13, h=12, full=True):
    p = Pic(w, h)
    m = p.ellipse(3.5, 3.6, 3.6, 3.6) | p.ellipse(8.5, 3.6, 3.6, 3.6) | p.poly([(0.2, 4.5), (11.8, 4.5), (6, 11.5)])
    if full:
        p.shade(m, "red", light=(-0.6, -0.8), bias=0.12)
        p.fill(p.rect(2, 2, 4, 3), ramp("red")[5])
    else:
        p.shade(m, ["#1a1a2e", "#2a2a46", "#3a3a5e"], light=(-0.6, -0.8), bias=0)
    p.outline(INK)
    return p


def scroll(frame, w=18, h=20):
    """A scroll of code: when it glows (frame 2) it shows it is ready to take."""
    p = Pic(w, h)
    body = p.rect(3, 3, 15, 17)
    p.shade(body, ["#8c7a4d", "#bba66c", "#e5d398", "#f9ecc0"], light=(-0.6, -0.8), roughness=0.05)
    for (y0, y1) in ((1, 5), (15, 19)):                       # rolls at top and bottom
        r = p.rect(1, y0, 17, y1)
        p.shade(r, "wood", light=(0, -1), bias=0.12)
        p.fill(p.rect(1, y0, 2, y1), ramp("wood")[5])
    g = ramp("blue")
    for y in (7, 9, 11, 13):                                 # lines of code
        p.fill(p.rect(5, y, 5 + (6 if y != 11 else 3), y + 1), g[1])
        p.fill(p.rect(5, y, 7, y + 1), g[3])
    p.outline(INK)
    if frame:
        glow = ndimage.binary_dilation(p.a[..., 3] > 0, iterations=2) & ~(p.a[..., 3] > 0)
        gp = ramp("gold")
        for y, x in zip(*np.nonzero(glow)):
            if BAYER[y % 4, x % 4] < 0.55:
                p.a[y, x] = (*gp[4], 255)
        for (x, y) in ((0, 2), (17, 6), (1, 16)):
            p.fill(p.rect(x, y, x + 1, y + 1), gp[5])
    return p


def sign(w=30, h=34):
    p = Pic(w, h)
    post = p.rect(13, 14, 17, h)
    p.shade(post, "wood", light=(-1, 0), roughness=0.1)
    p.outline(INK)
    board = p.rect(2, 2, w - 2, 18)
    p.shade(board, "wood", light=(-0.4, -1), roughness=0.06, bias=0.08)
    wd = ramp("wood")
    p.fill(p.rect(2, 2, w - 2, 3), wd[5])
    p.fill(p.rect(2, 17, w - 2, 18), wd[0])
    for x in (5, w - 7):
        p.fill(p.rect(x, 5, x + 1, 6), wd[0])
    # a tiny arrow
    p.fill(p.poly([(8, 10), (19, 10), (19, 7), (25, 11), (19, 15), (19, 12), (8, 12)]), wd[0])
    p.outline(INK)
    return p


def robot_echo(frame, w=40, h=54):
    """Echo, the friendly guide robot (frame 0 normal, 1 blinks and waves)."""
    p = Pic(w, h)
    cx = 20
    # legs and feet
    for x0 in (12, 23):
        leg = p.rect(x0, 38, x0 + 6, 48)
        p.shade(leg, "metal", light=(-1, 0), bias=0.05)
        foot = p.rect(x0 - 2, 46, x0 + 8, 53)
        p.shade(foot, "blue", light=(-0.4, -1), bias=0.1)
    # body
    body = p.rect(8, 22, 32, 41)
    p.shade(body, "metal", light=(-0.6, -0.8), roughness=0.05, bias=0.1)
    p.fill(p.rect(12, 27, 28, 36), ramp("metal")[0])          # chest screen
    p.fill(p.rect(13, 28, 27, 35), ramp("blue")[1])
    for i, y in enumerate((29, 31, 33)):                      # scrolling code lines
        p.fill(p.rect(15, y, 15 + (8, 11, 5)[i], y + 1), ramp("blue")[4])
    # arms
    p.shade(p.rect(3, 24, 8, 36), "metal", light=(-1, 0), bias=0.05)
    if frame:
        p.shade(p.poly([(32, 26), (38, 12), (42, 14), (36, 30)]), "metal", light=(-1, 0), bias=0.05)
        p.shade(p.ellipse(40, 11, 4, 4), "blue", bias=0.12)
    else:
        p.shade(p.rect(32, 24, 37, 36), "metal", light=(-1, 0), bias=0.05)
    p.shade(p.ellipse(5, 38, 4, 4), "blue", bias=0.12)
    if not frame:
        p.shade(p.ellipse(34, 38, 4, 4), "blue", bias=0.12)
    # head
    head = p.rect(7, 5, 33, 22)
    p.shade(head, "metal", light=(-0.6, -0.9), roughness=0.04, bias=0.12)
    face = p.rect(10, 8, 30, 19)
    p.fill(face, ramp("metal")[0])
    p.fill(p.rect(11, 9, 29, 18), ramp("blue")[0])
    if frame:
        for x in (14, 23):                                    # happy closed eyes ^ ^
            p.fill(p.rect(x, 12, x + 1, 13), ramp("blue")[5])
            p.fill(p.rect(x + 1, 11, x + 3, 12), ramp("blue")[5])
            p.fill(p.rect(x + 3, 12, x + 4, 13), ramp("blue")[5])
    else:
        for x in (14, 23):
            p.fill(p.rect(x, 11, x + 4, 15), ramp("blue")[4])
            p.fill(p.rect(x + 1, 11, x + 3, 12), ramp("blue")[5])
    p.fill(p.rect(16, 16, 24, 17), ramp("blue")[3])             # smile
    p.fill(p.rect(15, 15, 16, 16), ramp("blue")[3])
    p.fill(p.rect(24, 15, 25, 16), ramp("blue")[3])
    # antenna
    p.fill(p.rect(19, 0, 21, 6), ramp("metal")[2])
    p.shade(p.ellipse(20, 2, 3, 3), "orange" if frame else "red", bias=0.15)
    # ears
    p.shade(p.rect(4, 10, 8, 18), "blue", light=(-1, 0), bias=0.1)
    p.shade(p.rect(32, 10, 36, 18), "blue", light=(-1, 0), bias=0.1)
    p.outline(INK)
    return p


def gate(frame, w=44, h=70):
    """The code gate: frame 0 closed (a glowing lock panel), 1 open (the arch is empty)."""
    p = Pic(w, h)
    pillar_l, pillar_r = p.rect(0, 6, 9, h), p.rect(w - 9, 6, w, h)
    for pl in (pillar_l, pillar_r):
        p.shade(pl, "stone", light=(-0.7, -0.5), roughness=0.08)
    arch = p.rect(0, 0, w, 14)
    p.shade(arch, "stone", light=(-0.4, -1), roughness=0.06, bias=0.06)
    for x in range(4, w - 4, 10):
        p.fill(p.rect(x, 3, x + 5, 4), ramp("stone")[5])
    p.shade(p.rect(5, 14, w - 5, 17), "gold", light=(0, -1), bias=0.05)
    inner = p.rect(9, 17, w - 9, h)
    if frame:
        p.vgrad(inner, [(255, 250, 215), (255, 229, 150), (255, 205, 90), (255, 172, 60)], 17, h, flip=True)
        for (x, y) in ((16, 30), (28, 44), (21, 58), (30, 24)):
            p.fill(p.rect(x, y, x + 2, y + 1), (255, 255, 255))
    else:
        p.shade(inner, ["#10151f", "#1b2434", "#2a364c", "#3a4a66"], light=(-0.6, -0.8), bias=-0.08)
        for y in range(20, h - 4, 6):
            p.fill(p.rect(11, y, w - 11, y + 1), (14, 18, 28))
        # the lock
        lk = p.rect(15, 38, 29, 52)
        p.shade(lk, "gold", light=(-0.6, -0.8), bias=0.1)
        p.fill(p.rect(20, 42, 24, 47), ramp("gold")[0])
        p.fill(p.rect(21, 46, 23, 50), ramp("gold")[0])
        arc = p.ellipse(22, 36, 6, 7) & ~p.ellipse(22, 36, 3.5, 4.5) & p.rect(0, 28, w, 39)
        p.shade(arc, "metal", light=(-0.6, -0.8), bias=0.1)
    p.outline(INK)
    return p


def portal(frame, w=36, h=64):
    """The exit portal: a swirl of light inside a ring of stone (3 frames)."""
    p = Pic(w, h)
    ring = p.ellipse(18, 32, 17, 31) & ~p.ellipse(18, 32, 12, 26)
    p.shade(ring, "stone", light=(-0.7, -0.7), roughness=0.08, bias=0.05)
    inner = p.ellipse(18, 32, 12, 26)
    ang = np.arctan2((p.yy - 32) / 26.0, (p.xx - 18) / 12.0)
    rad = np.sqrt(((p.xx - 18) / 12.0) ** 2 + ((p.yy - 32) / 26.0) ** 2)
    t = 0.5 + 0.5 * np.sin(3 * ang + 5 * rad - frame * 2.1)
    t = np.clip(t * 0.8 + 0.2 * (1 - rad), 0, 0.999)
    cols = ramp("purple")
    v = t * (len(cols) - 1)
    b = np.floor(v)
    idx = np.clip(b + ((v - b) > BAYER[p.yy % 4, p.xx % 4]), 0, len(cols) - 1).astype(int)
    p.a[inner, :3] = np.array(cols, dtype="uint8")[idx][inner]
    p.a[inner, 3] = 255
    for (x, y) in ((18, 16), (12, 30), (24, 40), (17, 48)):
        p.fill(p.rect(x + frame, y - frame, x + frame + 1, y - frame + 1), (255, 255, 255))
    p.outline(INK)
    return p


def door(colour, locked=False, w=34, h=56):
    p = Pic(w, h)
    frame = p.rect(0, 0, w, h) & ~p.rect(6, 10, w - 6, h)
    arch = p.ellipse(17, 14, 17, 14) & p.rect(0, 0, w, 14)
    f = frame | arch
    p.shade(f, "stone", light=(-0.6, -0.8), roughness=0.08)
    inner = (p.rect(6, 12, w - 6, h) | p.ellipse(17, 14, 11, 10)) & ~p.rect(0, 0, w, 4)
    inner &= ~(p.ellipse(17, 14, 11, 10) == False) | p.rect(6, 14, w - 6, h)
    inner = p.rect(6, 14, w - 6, h) | p.ellipse(17, 14, 11, 10)
    if locked:
        p.shade(inner, ["#0c1020", "#151b32", "#202845", "#2b3558"], light=(-0.6, -0.8), bias=-0.05)
        lk = p.rect(11, 32, 23, 44)
        p.shade(lk, "gold", light=(-0.6, -0.8), bias=0.05)
        p.fill(p.rect(16, 36, 18, 40), ramp("gold")[0])
        arc = p.ellipse(17, 30, 5, 6) & ~p.ellipse(17, 30, 2.8, 3.8) & p.rect(0, 24, w, 33)
        p.shade(arc, "metal", light=(-0.6, -0.8), bias=0.1)
    else:
        c = ramp(colour)
        p.vgrad(inner, [c[5], c[4], c[3], c[2]], 10, h, flip=True)
        for (x, y) in ((12, 26), (22, 38), (16, 46), (24, 20)):
            p.fill(p.rect(x, y, x + 2, y + 1), (255, 255, 255))
    p.shade(p.rect(2, 52, w - 2, h), "stone", light=(0, -1), bias=0.05)
    p.outline(INK)
    return p


def tower(frame, w=34, h=88):
    """A server tower with blinking lights: the wallpaper of the hub (2 frames)."""
    p = Pic(w, h)
    body = p.rect(2, 4, w - 2, h)
    p.shade(body, "metal", light=(-0.6, -0.4), roughness=0.03, bias=-0.1)
    rng = random.Random(21)
    for i, y in enumerate(range(8, h - 6, 12)):
        p.fill(p.rect(5, y, w - 5, y + 9), ramp("metal")[0])
        p.fill(p.rect(5, y + 9, w - 5, y + 10), ramp("metal")[4])
        for k in range(4):
            on = (rng.random() < 0.55) ^ bool(frame and (i + k) % 3 == 0)
            col = ramp(["green", "blue", "orange"][(i + k) % 3])
            p.fill(p.rect(8 + k * 5, y + 3, 11 + k * 5, y + 6), col[4 if on else 1])
        p.fill(p.rect(w - 12, y + 3, w - 7, y + 4), ramp("metal")[3])
        p.fill(p.rect(w - 12, y + 5, w - 7, y + 6), ramp("metal")[3])
    p.outline(INK)
    return p


def bug(frame, w=30, h=22):
    """A glitch bug that patrols the platforms (2 frames: legs move)."""
    p = Pic(w, h)
    body = p.ellipse(15, 11, 13, 9) & ~p.rect(0, 17, w, h)
    p.shade(body, "bug", light=(-0.6, -0.9), roughness=0.08, bias=0.08)
    lg = ramp("bug")[1]
    for i, x in enumerate((6, 12, 18, 24)):
        up = (i + frame) % 2
        p.fill(p.rect(x, 17, x + 2, 20 + (0 if up else 1)), lg)
        p.fill(p.rect(x - 1 + (up), 19, x + 2 + (up), 21 if not up else 20), lg)
    p.fill(p.ellipse(9, 8, 4, 4), (255, 255, 255))
    p.fill(p.ellipse(20, 8, 4, 4), (255, 255, 255))
    p.fill(p.rect(9, 7, 11, 10), (20, 10, 40))
    p.fill(p.rect(19, 7, 21, 10), (20, 10, 40))
    p.fill(p.rect(8, 3, 12, 4), ramp("bug")[0])                 # angry brows
    p.fill(p.rect(19, 3, 23, 4), ramp("bug")[0])
    for x in (13, 17):
        p.fill(p.rect(x, 14, x + 1, 16), (255, 255, 255))      # little teeth
    p.fill(p.rect(5, 12, 7, 13), ramp("bug")[5])
    p.fill(p.rect(21, 14, 24, 15), ramp("bug")[1])
    p.outline(INK)
    return p


def flag(frame, w=22, h=42):
    p = Pic(w, h)
    pole = p.rect(3, 2, 5, h)
    p.shade(pole, "metal", light=(-1, 0), bias=0.1)
    p.shade(p.ellipse(4, 2, 3, 3), "gold", bias=0.15)
    wave = [0, 1, 0, -1][frame * 2 % 4]
    cloth = p.poly([(5, 6), (20, 7 + wave), (16, 12), (20, 17 - wave), (5, 18)])
    p.shade(cloth, "green", light=(-0.6, -0.8), bias=0.08)
    p.fill(p.rect(8, 10, 10, 14), ramp("green")[5])           # a tiny check mark
    p.fill(p.rect(10, 12, 12, 13), ramp("green")[5])
    p.shade(p.rect(0, h - 4, 10, h), "stone", light=(0, -1), bias=0.05)
    p.outline(INK)
    return p


def goal(frame, w=56, h=80):
    """The Compiler Gate that ends a world: a green archway with a glowing HL on it (2 frames pulse)."""
    p = Pic(w, h)
    base = p.rect(0, 0, w, h) & ~p.rect(9, 18, w - 9, h)
    arch = p.ellipse(28, 24, 28, 24) & p.rect(0, 0, w, 24)
    p.shade(base | arch, "stone", light=(-0.6, -0.8), roughness=0.07)
    inner = p.rect(9, 24, w - 9, h) | p.ellipse(28, 24, 19, 16)
    g = ramp("green")
    p.vgrad(inner, [g[5], g[4], g[3], g[2]] if frame else [g[4], g[3], g[2], g[1]], 8, h, flip=True)
    for (x, y) in ((16, 40), (36, 52), (24, 62), (40, 34)):
        p.fill(p.rect(x, y, x + 2, y + 1), (255, 255, 255))
    p.shade(p.rect(0, h - 5, w, h), "stone", light=(0, -1), bias=0.05)
    # the HL badge on top of the arch
    badge = p.ellipse(28, 7, 9, 7)
    p.shade(badge, "blue", light=(-0.6, -0.8), bias=0.12)
    p.fill(p.rect(22, 4, 24, 11), (255, 255, 255))
    p.fill(p.rect(26, 4, 28, 11), (255, 255, 255))
    p.fill(p.rect(22, 7, 28, 8), (255, 255, 255))
    p.fill(p.rect(30, 4, 32, 11), ramp("blue")[5])
    p.fill(p.rect(30, 9, 35, 11), ramp("blue")[5])
    p.outline(INK)
    return p


def padlock(w=11, h=13):
    p = Pic(w, h)
    p.shade(p.rect(1, 6, 10, 13), "gold", light=(-0.6, -0.8), bias=0.1)
    arc = p.ellipse(5.5, 5, 4, 4.5) & ~p.ellipse(5.5, 5, 2, 2.6) & p.rect(0, 0, w, 7)
    p.shade(arc, "metal", light=(-0.6, -0.8), bias=0.1)
    p.fill(p.rect(5, 8, 7, 11), ramp("gold")[0])
    p.outline(INK)
    return p


def star(w=11, h=11, colour="gold"):
    p = Pic(w, h)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 5.2 if i % 2 == 0 else 2.3
        pts.append((5 + r * math.cos(a), 5.5 + r * math.sin(a)))
    p.shade(p.poly(pts), colour, light=(-0.6, -0.8), bias=0.15)
    p.outline(INK)
    return p
