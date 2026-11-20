"""Art for the redesigned Motherboard hub (pixel size 1): city skylines that light up as worlds are finished, a chip tower,
seven arched portal doors that show a peek of their world, glowing floor tiles and small props."""
import math
import random
import numpy as np
from art import Pic, ramp, rgb, RAMPS, INK, tile_circuit

RAMPS["cityfar"] = ["#070d2e", "#0b1644", "#101f5c", "#162a78"]
RAMPS["citynear"] = ["#0a1648", "#10286e", "#193c9c", "#2556c8", "#3f7af0"]
RAMPS["arch"] = ["#14193a", "#252d5c", "#3b4888", "#5767b0", "#8497dc", "#c5d2ff"]
CYAN = (96, 226, 255)
LIT = [(255, 214, 110), (255, 238, 170), (120, 232, 255)]
THR = (0.10, 0.38, 0.72)


def _buildings(w, lo, hi, seed, narrow=(20, 46)):
    rng = random.Random(seed)
    out, x = [], 0
    while x < w:
        bw = rng.randrange(*narrow)
        if w - (x + bw) < narrow[0]:
            bw = w - x
        out.append((x, bw, rng.randrange(lo, hi), rng.randrange(0, 5)))
        x += bw
    return out


def skyline_far(w=480, h=140, seed=11):
    p = Pic(w, h)
    rng = random.Random(seed)
    for cx, cy, rx, ry in [(rng.randrange(0, w), rng.randrange(10, 70), rng.randrange(26, 60), rng.randrange(8, 16)) for _ in range(11)]:
        for ox in (-w, 0, w):
            m = p.ellipse(cx + ox, cy, rx, ry)
            p.shade(m, ["#0c1650", "#131f6c", "#1b2a88"], light=(-0.3, -1), roughness=0.05, seed=cx)
    for x, bw, bh, kind in _buildings(w, 40, h - 10, seed, (18, 40)):
        body = p.rect(x, h - bh, x + bw, h)
        p.shade(body, "cityfar", light=(-0.7, -0.2), roughness=0.03, bias=-0.1)
        p.fill(p.rect(x, h - bh, x + bw, h - bh + 1), rgb("#2a44a8"))
        for wy in range(h - bh + 6, h - 4, 7):
            for wx in range(x + 4, x + bw - 3, 6):
                if rng.random() < 0.18:
                    p.fill(p.rect(wx, wy, wx + 2, wy + 2), rgb("#3a64d8"))
        if kind == 0:
            p.fill(p.rect(x + bw // 2, h - bh - 12, x + bw // 2 + 1, h - bh), rgb("#2a44a8"))
    return p


def skyline_near(frame, w=480, h=112, seed=7):
    p = Pic(w, h)
    rng = random.Random(seed)
    thr = THR[frame]
    bright = (0.5, 0.78, 1.0)[frame]
    for x, bw, bh, kind in _buildings(w, 36, h - 8, seed, (24, 54)):
        top = h - bh
        body = p.rect(x, top, x + bw, h)
        p.shade(body, "citynear", light=(-0.7, -0.3), roughness=0.04, bias=-0.1)
        p.fill(p.rect(x, top, x + bw, top + 1), rgb("#6f9bff"))          # a lit roof edge
        p.fill(p.rect(x, top, x + 1, h), rgb("#08113a"))                 # a dark seam between buildings
        if kind == 1:                                                     # a stepped top
            p.shade(p.rect(x + 4, top - 8, x + bw - 4, top), "citynear", light=(-0.7, -0.3), bias=-0.05)
            p.fill(p.rect(x + 4, top - 8, x + bw - 4, top - 7), rgb("#6f9bff"))
        if kind == 2:                                                     # an antenna with a beacon
            ax = x + bw // 2
            p.fill(p.rect(ax, top - 14, ax + 1, top), rgb("#6f9bff"))
            p.fill(p.rect(ax - 1, top - 16, ax + 2, top - 13), (255, 90, 90) if frame else (110, 40, 60))
        if kind == 3:                                                     # a dome
            p.shade(p.ellipse(x + bw / 2, top, bw / 2 - 3, 8) & ~p.rect(0, top, w, h), "citynear", light=(-0.5, -0.9), bias=0.05)
        for wy in range(top + 5, h - 3, 6):
            for wx in range(x + 4, x + bw - 3, 6):
                v = rng.random()
                col = LIT[rng.randrange(0, 3)]
                if v < thr:
                    p.fill(p.rect(wx, wy, wx + 3, wy + 3), col)
                else:
                    p.fill(p.rect(wx, wy, wx + 3, wy + 3), rgb("#0a1a58"))
        if rng.random() < 0.55:                                           # a circuit line down the building
            tx = x + 3 + rng.randrange(0, max(1, bw - 7))
            colr = tuple(int(c * bright) for c in CYAN)
            p.fill(p.rect(tx, top + 2, tx + 1, h), colr)
            ny = top + 8 + rng.randrange(0, 20)
            p.fill(p.rect(tx, ny, min(tx + 8, x + bw - 1), ny + 1), colr)
            p.fill(p.rect(min(tx + 8, x + bw - 2), ny - 1, min(tx + 10, x + bw), ny + 2), colr)
    return p


def chip_tower(frame, w=76, h=150):
    p = Pic(w, h)
    body = p.rect(12, 30, w - 12, h)
    p.shade(body, "citynear", light=(-0.7, -0.3), roughness=0.03, bias=-0.1)
    p.shade(p.rect(22, 8, w - 22, 36), "citynear", light=(-0.7, -0.3), bias=-0.05)
    p.fill(p.rect(37, 0, 39, 10), rgb("#6f9bff"))
    p.fill(p.rect(36, 0, 40, 3), (255, 90, 90))
    for x0, y0, x1 in ((2, 70, 14), (w - 14, 84, w - 2), (4, 100, 14), (w - 14, 112, w - 4)):
        p.shade(p.rect(x0, y0, x1, h), "citynear", light=(-0.7, -0.3), bias=-0.12)
    # the chip: a glowing square in the middle of the tower
    cx, cy = w // 2, 56
    p.fill(p.rect(cx - 15, cy - 15, cx + 15, cy + 15), rgb("#0a2a70"))
    for k in range(-12, 13, 6):
        p.fill(p.rect(cx + k, cy - 18, cx + k + 2, cy - 15), rgb("#7fd6ff"))
        p.fill(p.rect(cx + k, cy + 15, cx + k + 2, cy + 18), rgb("#7fd6ff"))
        p.fill(p.rect(cx - 18, cy + k, cx - 15, cy + k + 2), rgb("#7fd6ff"))
        p.fill(p.rect(cx + 15, cy + k, cx + 18, cy + k + 2), rgb("#7fd6ff"))
    p.shade(p.rect(cx - 11, cy - 11, cx + 11, cy + 11), ["#1480d6", "#2eb2f5", "#7fd6ff", "#dcf4ff"] if frame else ["#0f4a95", "#1480d6", "#2eb2f5", "#7fd6ff"], light=(-0.5, -0.8))
    p.fill(p.rect(cx - 6, cy - 6, cx + 6, cy + 6), rgb("#dcf4ff") if frame else rgb("#7fd6ff"))
    p.fill(p.rect(cx - 3, cy - 3, cx + 3, cy + 3), rgb("#ffffff") if frame else rgb("#bfe8ff"))
    # traces running down and out of the chip
    c1 = rgb("#4fd2ff") if frame else rgb("#2a7ec8")
    p.fill(p.rect(cx - 1, cy + 18, cx + 1, h), c1)
    for ty, dx in ((92, 16), (108, -16), (124, 20)):
        p.fill(p.rect(min(cx, cx + dx), ty, max(cx, cx + dx), ty + 1), c1)
        p.fill(p.rect(cx + dx - 1, ty - 2, cx + dx + 2, ty + 3), c1)
    for wy in range(38, 46, 4):
        for wx in range(26, w - 24, 6):
            p.fill(p.rect(wx, wy, wx + 3, wy + 2), (255, 214, 110))
    p.outline(rgb("#07103a"))
    return p


# ------------------------------------------------------------------------------------------------ floor tiles
def tile_hub(top=True, seed=3, alt=False):
    p = Pic(16, 16)
    m = np.ones((16, 16), bool)
    p.shade(m, ["#0a1244", "#10206a", "#183090", "#2144b8"], light=(-0.3, -1), roughness=0.04, seed=seed, bias=-0.15)
    ar = ramp("arch")
    if top:
        p.fill(p.rect(0, 0, 16, 1), rgb("#9fb4ff"))
        p.fill(p.rect(0, 1, 16, 3), ar[3])
        p.fill(p.rect(0, 3, 16, 4), ar[1])
        p.fill(p.rect(0 if not alt else 8, 0, 1 if not alt else 9, 4), ar[0])          # a seam between the paving stones
        p.fill(p.rect(1, 6, 15, 7), (30, 150, 230))                                       # a glowing trace
        p.fill(p.rect(1, 7, 15, 8), (14, 60, 150))
        p.fill(p.rect(7 if not alt else 3, 5, 10 if not alt else 6, 9), (127, 214, 255))
    else:
        c = (30, 150, 230)
        p.fill(p.rect(2, 5, 14, 6), c)
        p.fill(p.rect(8 if not alt else 4, 6, 9 if not alt else 5, 13), c)
        p.fill(p.rect(7 if not alt else 3, 12, 10 if not alt else 6, 15), (127, 214, 255))
        p.fill(p.rect(1, 1, 3, 3), (70, 100, 200))
        p.fill(p.rect(13, 1, 15, 3), (70, 100, 200))
        p.fill(p.rect(0, 15, 16, 16), rgb("#060a28"))
    return p


# ------------------------------------------------------------------------------------------------ portal doors
GEMS = ["#3fd477", "#ff9a2a", "#ff5a4a", "#e063e8", "#7fd6ff", "#ff2a4a", "#ffd95c"]
DW, DH = 50, 72


def _scene(i, shimmer):
    s = Pic(DW, DH)
    full = s.rect(0, 0, DW, DH)
    r = random.Random(i * 7 + shimmer)
    if i == 1:
        s.vgrad(full, ["#3f8fe0", "#6fb4f0", "#a9d8f8", "#dff2fd"], 6, 64)
        s.shade(s.ellipse(14, 72, 26, 16), "grass", light=(-0.5, -1), roughness=0.05)
        s.shade(s.ellipse(42, 74, 22, 14), "leaf", light=(-0.5, -1), roughness=0.05)
        s.shade(s.rect(32, 50, 36, 66), "wood", light=(-1, 0))
        s.shade(s.ellipse(34, 44, 9, 9), "leaf", light=(-0.6, -0.8), roughness=0.08)
        s.fill(s.ellipse(15 + shimmer * 2, 24, 7, 3), (255, 255, 255))
        s.fill(s.ellipse(20 + shimmer * 2, 22, 5, 3), (255, 255, 255))
    elif i == 2:
        s.vgrad(full, ["#3a1408", "#923b0e", "#d26414", "#f9902a", "#ffd08a"], 6, 66)
        d = (44, 22, 20)
        s.fill(s.rect(10, 38, 17, 68), d)
        s.fill(s.rect(8, 36, 19, 40), d)
        for k, (cx, cy, rr) in enumerate(((13, 30 - shimmer, 4), (16, 24 - shimmer, 5), (12, 17 - shimmer, 5))):
            s.fill(s.ellipse(cx, cy, rr, rr - 1), (92, 70, 70))
        s.fill(s.rect(24, 52, 46, 68), d)
        g = s.ellipse(35, 48, 9, 9)
        for a in range(0, 360, 45):
            tx, ty = 35 + 10 * math.cos(math.radians(a + shimmer * 22)), 48 + 10 * math.sin(math.radians(a + shimmer * 22))
            g |= s.ellipse(tx, ty, 2.2, 2.2)
        s.fill(g, d)
        s.fill(s.ellipse(35, 48, 3, 3), (249, 144, 42))
    elif i == 3:
        s.vgrad(full, ["#3a0c14", "#a3263a", "#e43a4c", "#ff9a5a", "#ffd08a"], 6, 66)
        d = (56, 24, 34)
        s.fill(s.rect(12, 52, 32, 68), d)
        s.fill(s.poly([(9, 53), (22, 38), (35, 53)]), (80, 30, 40))
        s.fill(s.rect(26, 40, 29, 50), d)
        s.fill(s.rect(16, 56, 21, 62), (255, 224, 140))
        s.fill(s.rect(36, 58, 46, 68), d)
        s.fill(s.poly([(34, 59), (41, 50), (48, 59)]), (80, 30, 40))
        s.fill(s.rect(40, 62, 43, 66), (255, 224, 140))
    elif i == 4:
        s.vgrad(full, ["#1c0c3e", "#3d1c86", "#6f3de0", "#b78aff"], 6, 66)
        s.fill(s.ellipse(25, 70, 22, 8), (122, 80, 210))
        s.shade(s.rect(14, 22, 36, 48), "gold", light=(-0.5, -0.8))
        s.fill(s.rect(17, 25, 33, 45), (36, 18, 74))
        s.fill(s.ellipse(25, 33, 5, 5), (255, 217, 92))
        s.fill(s.poly([(17, 45), (25, 36), (33, 45)]), (63, 212, 119))
        for px in (10, 40):
            s.shade(s.rect(px, 56, px + 2, 68), "gold", light=(-1, 0))
            s.fill(s.ellipse(px + 1, 56, 2, 2), rgb("#ffd95c"))
        s.line([(11, 58), (20, 62), (30, 62), (41, 58)], (228, 58, 76), 1)
    elif i == 5:
        s.vgrad(full, ["#7fb6ee", "#b9dcf8", "#e8f6ff", "#ffffff"], 6, 64)
        s.shade(s.poly([(4, 62), (18, 28), (34, 62)]), "snow", light=(-0.6, -0.7))
        s.shade(s.poly([(22, 64), (35, 38), (50, 64)]), "snow", light=(-0.6, -0.7), bias=0.1)
        s.fill(s.rect(0, 60, DW, DH), (240, 248, 255))
        for px, py in ((12, 62), (40, 63), (26, 66)):
            s.fill(s.poly([(px, py - 14), (px - 5, py), (px + 5, py)]), (31, 107, 82))
            s.fill(s.poly([(px, py - 14), (px - 2, py - 9), (px + 2, py - 9)]), (240, 248, 255))
    elif i == 6:
        s.vgrad(full, ["#12030a", "#4a0c22", "#841834", "#d03040"], 6, 66)
        d = (22, 8, 30)
        s.fill(s.rect(14, 44, 36, 68), d)
        for tx, hh in ((11, 36), (22, 22), (33, 38)):
            s.fill(s.rect(tx, 70 - hh - 24, tx + 7, 68), d)
            s.fill(s.poly([(tx - 1, 70 - hh - 24), (tx + 3.5, 70 - hh - 34), (tx + 8, 70 - hh - 24)]), d)
        for ex in (20, 27):
            s.fill(s.rect(ex, 52, ex + 2, 55 + shimmer), (255, 217, 92))
        s.fill(s.rect(22, 60, 28, 68), (60, 10, 20))
    else:
        for y in range(DH):
            for x in range(DW):
                d_ = math.hypot(x - 25, y - 70)
                band = int((d_ - 18) // 4)
                cols = [(255, 140, 160), (255, 190, 130), (255, 236, 140), (160, 235, 160), (140, 220, 250), (190, 160, 250)]
                if 0 <= band < len(cols):
                    s.a[y, x] = (*cols[band], 255)
                else:
                    t = min(1.0, y / 70)
                    s.a[y, x] = (int(255 - 70 * t), int(220 - 40 * t), int(250 - 30 * t), 255)
        s.fill(s.ellipse(14, 68, 14, 8), (255, 255, 255))
        s.fill(s.ellipse(38, 70, 16, 9), (255, 255, 255))
        for k in range(5):
            sx, sy = r.randrange(10, 40), r.randrange(10, 40)
            s.fill(s.rect(sx, sy, sx + 1, sy + 3), (255, 255, 255))
            s.fill(s.rect(sx - 1, sy + 1, sx + 2, sy + 2), (255, 255, 255))
    return s


def portal_door(i, state):
    """state 0 and 1: the world waits (a gentle shimmer); state 2: finished (lit up)."""
    p = Pic(DW, DH)
    outer = p.rect(0, 25, DW, DH) | p.ellipse(25, 25, 25, 25)
    inner = p.rect(6, 25, DW - 6, DH - 4) | p.ellipse(25, 25, 19, 19)
    inner &= ~p.rect(0, DH - 4, DW, DH)
    p.shade(outer, "arch", light=(-0.5, -0.9), roughness=0.04, bias=0.02)
    p.fill(p.rect(0, DH - 6, DW, DH), rgb("#252d5c"))
    p.fill(p.rect(0, DH - 6, DW, DH - 5), rgb("#8497dc"))
    scene = _scene(i, state % 2)
    if state == 2:
        scene.a[..., :3] = np.clip(scene.a[..., :3].astype(int) * 1.0 + 38, 0, 255).astype("uint8")
    p.a[inner] = scene.a[inner]
    edge = ((p.xx - 25) ** 2 + (p.yy - 25) ** 2 <= 20 ** 2) | (p.yy >= 25)
    ring = inner & ~(p.rect(7, 25, DW - 7, DH - 5) | p.ellipse(25, 25, 18, 18))
    p.fill(ring, rgb("#07103a"))                                     # the dark inner edge of the arch
    for x, y in ((3, 40), (46, 40), (3, 58), (46, 58)):               # rivets
        p.fill(p.rect(x, y, x + 2, y + 2), rgb("#14193a"))
        p.fill(p.rect(x, y, x + 1, y + 1), rgb("#c5d2ff"))
    g = rgb(GEMS[i - 1])
    gem = p.ellipse(25, 4, 4, 4)
    p.fill(p.ellipse(25, 4, 6, 6), rgb("#14193a"))
    p.fill(gem, g)
    p.fill(p.rect(24, 3, 25, 4), (255, 255, 255))
    if state == 2:
        glow = tuple(min(255, int(c * 0.6 + 100)) for c in g)
        for dx, dy in ((-8, 0), (8, 0), (0, -5), (-6, -4), (6, -4)):
            p.fill(p.rect(25 + dx, 4 + dy, 26 + dx, 5 + dy), glow)
    p.outline(rgb("#07103a"))
    return p


# ------------------------------------------------------------------------------------------------ props
def terminal(w=34, h=38):
    p = Pic(w, h)
    p.shade(p.rect(12, 28, 22, 36), "arch", light=(-0.5, -1))
    p.shade(p.rect(6, 34, 28, h), "arch", light=(-0.5, -1))
    p.shade(p.rect(1, 2, w - 1, 30), "arch", light=(-0.4, -1))
    p.fill(p.rect(4, 5, w - 4, 27), rgb("#061a4a"))
    p.fill(p.rect(4, 5, w - 4, 6), rgb("#1a3a8a"))
    p.fill(p.rect(9, 11, 13, 17), (127, 230, 255))
    p.fill(p.rect(21, 11, 25, 17), (127, 230, 255))
    p.fill(p.rect(10, 20, 24, 22), (127, 230, 255))
    p.fill(p.rect(8, 18, 10, 20), (127, 230, 255))
    p.fill(p.rect(24, 18, 26, 20), (127, 230, 255))
    p.outline(INK)
    return p


def dish(frame, w=40, h=52):
    p = Pic(w, h)
    p.shade(p.rect(17, 24, 23, h), "arch", light=(-0.8, -0.2))
    p.shade(p.rect(10, h - 8, 30, h), "arch", light=(-0.5, -1))
    bowl = p.ellipse(20, 16, 17, 13) & ~p.rect(0, 16, w, h)
    bowl |= p.ellipse(20, 16, 17, 6)
    p.shade(bowl, "arch", light=(-0.6, -0.9), bias=0.05)
    p.fill(p.rect(19, 0, 21, 16), rgb("#8497dc"))
    p.fill(p.rect(18, 0, 22, 3), (255, 90, 90) if frame else (110, 40, 60))
    p.outline(INK)
    return p


def fern(frame, w=20, h=24):
    p = Pic(w, h)
    rng = random.Random(4)
    for k in range(7):
        a = math.radians(-90 + (k - 3) * 22)
        for t in range(2, 20):
            x = 10 + math.cos(a) * t * 0.5 + (k - 3) * 0.2 * t * 0.3
            y = h - 3 - abs(math.sin(a)) * t * 0.95 + (t * t) * 0.01 * abs(k - 3)
            p.fill(p.rect(int(x), int(y), int(x) + 2, int(y) + 2), rgb(["#1c6b5c", "#2ba58a", "#59d8b0"][t % 3]))
    for x, y in ((6, 9), (14, 6), (10, 3)):
        p.fill(p.ellipse(x + 0.5, y + (1 if frame else 0), 1.5, 1.5), (127, 230, 255))
    p.shade(p.rect(5, h - 5, 15, h), "arch", light=(-0.5, -1))
    p.outline(INK)
    return p
