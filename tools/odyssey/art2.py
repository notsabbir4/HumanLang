"""More pixel-size-1 art for Odyssey worlds 2, 3, 4, 6 and 7: factory tiles, town houses, gears, the boss and its bolts."""
import random
import numpy as np
from art import Pic, ramp, INK, RAMPS

RAMPS["roofred"] = ["#3a0c14", "#6b1624", "#a3263a", "#d44458", "#f27a86", "#ffc0c6"]
RAMPS["roofblue"] = ["#0c1c3a", "#173a6b", "#2760a3", "#3f8fd4", "#76bff2", "#c0e4ff"]
RAMPS["plaster"] = ["#6b5a48", "#9c8870", "#c9b394", "#e6d3b0", "#f6e8cd", "#fff6e3"]
RAMPS["plaster2"] = ["#4a5a6b", "#6f849a", "#97aec4", "#bdd0e0", "#dbe8f2", "#f4faff"]
RAMPS["warn"] = ["#5a1a08", "#a0320c", "#e0561a", "#ff8a2a", "#ffc04a", "#fff0a0"]


def tile_metal(top=True, seed=3):
    p = Pic(16, 16)
    m = np.ones((16, 16), bool)
    p.shade(m, "metal", light=(-0.3, -1), roughness=0.05, seed=seed, bias=-0.12)
    mt = ramp("metal")
    p.fill(p.rect(0, 15, 16, 16), mt[0])
    p.fill(p.rect(0, 7, 16, 8), mt[0])
    p.fill(p.rect(0, 8, 16, 9), mt[3])
    for x, y in ((2, 2), (13, 2), (2, 11), (13, 11)):
        p.fill(p.rect(x, y, x + 2, y + 2), mt[0])
        p.fill(p.rect(x, y, x + 1, y + 1), mt[5])
    if top:
        w = ramp("warn")
        for x in range(0, 16):
            on = ((x // 4) % 2 == 0)
            p.fill(p.rect(x, 0, x + 1, 3), w[3] if on else (24, 28, 48))
        p.fill(p.rect(0, 3, 16, 4), mt[0])
    return p


def house(kind=0, w=64, h=70):
    p = Pic(w, h)
    wall = "plaster" if kind == 0 else "plaster2"
    roof = "roofred" if kind == 0 else "roofblue"
    body = p.rect(6, 30, w - 6, h)
    p.shade(body, wall, light=(-0.5, -0.7), roughness=0.05, bias=0.05)
    p.outline(INK)
    r = p.poly([(0, 34), (w // 2, 4), (w, 34)])
    p.shade(r, roof, light=(-0.5, -1), roughness=0.05, bias=0.02)
    rc = ramp(roof)
    for y in range(10, 34, 5):
        p.fill(p.rect(2, y, w - 2, y + 1), rc[1]) if False else None
    for x in range(8, w - 6, 8):
        pass
    p.outline(INK)
    wd = ramp("wood")
    p.shade(p.rect(w // 2 - 7, 46, w // 2 + 7, h), "wood", light=(-0.5, -0.5), roughness=0.08)
    p.fill(p.rect(w // 2 + 3, 58, w // 2 + 5, 60), ramp("gold")[4])
    p.outline(INK)
    for cx in (16, w - 24):
        p.fill(p.rect(cx, 40, cx + 9, 50), (255, 224, 140))
        p.fill(p.rect(cx, 40, cx + 9, 41), wd[1])
        p.fill(p.rect(cx, 49, cx + 9, 50), wd[1])
        p.fill(p.rect(cx + 4, 40, cx + 5, 50), wd[1])
        p.fill(p.rect(cx, 44, cx + 9, 45), wd[1])
    p.fill(p.rect(w // 2 + 14, 14, w // 2 + 20, 30), ramp("stone")[2])
    p.outline(INK)
    return p


def gear(frame, w=30, h=30):
    p = Pic(w, h)
    cx = cy = 15
    teeth = np.zeros((h, w), bool)
    ang = np.arctan2(p.yy - cy, p.xx - cx) + (0.26 if frame else 0)
    rad = np.hypot(p.xx - cx, p.yy - cy)
    toothed = rad <= 10 + 3.5 * (np.cos(ang * 8) > 0)
    p.shade(toothed, "metal", light=(-0.6, -0.8), roughness=0.04, bias=0.0)
    p.fill(p.ellipse(cx, cy, 5, 5), ramp("metal")[0])
    p.fill(p.ellipse(cx - 1, cy - 1, 2, 2), ramp("metal")[4])
    p.outline(INK)
    return p


def crate(w=24, h=24):
    p = Pic(w, h)
    p.shade(p.rect(0, 0, w, h), "wood", light=(-0.4, -0.8), roughness=0.08)
    wd = ramp("wood")
    p.fill(p.rect(0, 0, w, 2), wd[0])
    p.fill(p.rect(0, h - 2, w, h), wd[0])
    p.fill(p.rect(0, 0, 2, h), wd[0])
    p.fill(p.rect(w - 2, 0, w, h), wd[0])
    for i in range(0, w - 4):
        p.fill(p.rect(2 + i, 2 + i * (h - 4) // (w - 4), 4 + i, 4 + i * (h - 4) // (w - 4)), wd[1])
    p.outline(INK)
    return p


def lamp(w=14, h=58):
    p = Pic(w, h)
    p.shade(p.rect(6, 14, 8, h), "metal", light=(-1, 0))
    p.shade(p.rect(3, h - 6, 11, h), "metal", light=(-0.5, -1))
    p.fill(p.ellipse(7, 8, 5, 6), (255, 236, 150))
    p.fill(p.ellipse(6, 7, 2, 3), (255, 252, 220))
    p.fill(p.rect(3, 13, 11, 15), ramp("metal")[1])
    p.outline(INK)
    return p


def boss(frame, w=64, h=72):
    """The Glitch King: a big purple bug with a crown (2 frames)."""
    p = Pic(w, h)
    body = p.ellipse(32, 44, 30, 26) & ~p.rect(0, 62, w, h)
    p.shade(body, "bug", light=(-0.6, -0.9), roughness=0.08, bias=0.08)
    lg = ramp("bug")[1]
    for i, x in enumerate((8, 20, 34, 46)):
        up = (i + frame) % 2
        p.fill(p.rect(x, 62, x + 6, 68 + (0 if up else 2)), lg)
        p.fill(p.rect(x - 2, 66, x + 8, 70 + (0 if up else 2)), lg)
    for ex in (21, 43):
        p.fill(p.ellipse(ex, 38, 8, 8), (255, 255, 255))
        p.fill(p.ellipse(ex + (1 if ex > 30 else -1) * 0 + 1, 40, 4, 4), (200, 20, 40))
        p.fill(p.rect(ex - 8, 28, ex + 8, 30), ramp("bug")[0])
    p.fill(p.rect(18, 52, 46, 55), ramp("bug")[0])
    for x in range(20, 46, 6):
        p.fill(p.rect(x, 55, x + 3, 59), (255, 255, 255))
    p.fill(p.rect(12, 38, 16, 42), ramp("bug")[5])
    g = ramp("gold")
    crown = p.poly([(14, 24), (14, 8), (23, 17), (32, 3), (41, 17), (50, 8), (50, 24)])
    p.shade(crown, "gold", light=(-0.5, -1), roughness=0.03)
    p.fill(p.rect(14, 22, 50, 24), g[1])
    for x, c in ((14, "red"), (32, "blue"), (50, "red")):
        p.fill(p.ellipse(min(x, 49) if x == 50 else x, 7 if x != 32 else 3, 2, 2), ramp(c)[4])
    p.outline(INK)
    return p


def bolt(frame, w=12, h=22):
    """An error bolt that falls from the sky (2 frames)."""
    p = Pic(w, h)
    pts = [(6, 0), (11, 8), (7, 8), (10, 16), (3, 16), (6, 11), (1, 11)] if False else [(7, 0), (1, 11), (5, 11), (3, 21), (11, 8), (7, 8), (10, 0)]
    r = ramp("red")
    p.shade(p.poly(pts), "red" if frame == 0 else "orange", light=(-0.5, -1), roughness=0.0)
    p.fill(p.rect(5, 6, 7, 10), r[5])
    p.outline(INK)
    return p


def warn(w=14, h=18):
    """The red marker that shows where a bolt is about to land."""
    p = Pic(w, h)
    t = p.poly([(7, 0), (13, 14), (1, 14)])
    p.shade(t, "warn", light=(-0.3, -1))
    p.fill(p.rect(6, 5, 8, 10), (60, 10, 10))
    p.fill(p.rect(6, 12, 8, 13), (60, 10, 10))
    p.outline(INK)
    return p


def easel(w=40, h=56):
    p = Pic(w, h)
    p.shade(p.rect(4, 12, 6, h), "wood", light=(-1, 0))
    p.shade(p.rect(w - 6, 12, w - 4, h), "wood", light=(-1, 0))
    p.shade(p.rect(2, 4, w - 2, 36), "wood", light=(-0.4, -1))
    p.fill(p.rect(5, 7, w - 5, 33), (246, 242, 230))
    for i, c in enumerate(("#E43A4C", "#2EB2F5", "#F0B832", "#3FD477")):
        p.fill(p.ellipse(12 + i * 6, 20, 3, 3), tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)))
    p.outline(INK)
    return p
