"""The hero: the HL mascot, converted from the project's own reaction pictures into pixel-size-1 frames."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
import numpy as np
from pixelkit import *

MASCOT = os.path.join(os.path.dirname(__file__), "..", "..", "website", "static", "mascot")
W, H = 64, 52          # the hero's canvas (pixels): the feet rest on the bottom edge


def clean_splash(im):
    """The jump picture has a water splash under the shoes: remove the pale-blue and white splash, keep the shoes."""
    a = np.array(im)
    h = a.shape[0]
    y0 = int(h * 0.80)
    r, g, b, al = (a[y0:, :, i].astype(int) for i in range(4))
    splash = (al > 0) & (b > 190) & (g > 150) & (r < 235) & (b - r > 40)
    a[y0:, :, 3] = np.where(splash, 0, a[y0:, :, 3])
    return Image.fromarray(a)


def pose(name, height, canvas=(W, H), dx=0, dy=0):
    im = trim(main_part(harden(load(os.path.join(MASCOT, name + ".png")))))
    w = round(im.width * height / im.height)
    return put(canvas[0], canvas[1], resize(im, w, height), dx, dy)


def run_frames():
    base = trim(main_part(harden(load(os.path.join(MASCOT, "run.png")))))
    h = 40
    a = resize(base, round(base.width * h / base.height), h)
    # a second running pose: the lower third (legs and shoes) swaps sides, and the body lifts one pixel
    legs_y = int(a.height * 0.62)
    top, bottom = a.crop((0, 0, a.width, legs_y)), a.crop((0, legs_y, a.width, a.height))
    b = Image.new("RGBA", a.size, (0, 0, 0, 0))
    b.alpha_composite(top, (0, 0))
    b.alpha_composite(bottom.transpose(Image.FLIP_LEFT_RIGHT), (0, legs_y))
    return put(W, H, a, 0, 0), put(W, H, b, 0, -1)


def frames():
    r1, r2 = run_frames()
    return {
        "idle": pose("thumbs", 46),
        "run1": r1,
        "run2": r2,
        "jump": pose("cheer", 48),
        "hurt": pose("oops", 46),
        "cheer": pose("party", 48),
    }


if __name__ == "__main__":
    f = frames()
    names = ["idle", "run1", "run2", "jump", "hurt", "cheer"]
    pal = palette_of([f[n] for n in names], 30)
    q = [Image.fromarray(np.where((remap(f[n], pal) >= 0)[..., None], np.array(pal)[np.clip(remap(f[n], pal), 0, None)], 0).astype("uint8")).convert("RGBA") for n in names]
    # alpha from the grid
    out = []
    for n in names:
        g = remap(f[n], pal)
        arr = np.zeros(g.shape + (4,), dtype="uint8")
        arr[g >= 0, :3] = np.array(pal)[g[g >= 0]]
        arr[g >= 0, 3] = 255
        out.append(Image.fromarray(arr))
    preview(out, "/tmp/g/od/hero.png", scale=5)
    print(len(pal), "colours")
