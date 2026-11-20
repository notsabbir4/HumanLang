"""The hero from the HL mascot sprite sheet (assets_src/mascot_sheet.png): run, jump and fall frames, pixel size 1."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
from scipy import ndimage
from pixelkit import load, trim, resize, put
import hero as old

SRC = os.path.join(os.path.dirname(__file__), "assets_src", "mascot_sheet.png")
# the pictures on the sheet: (left, top, right, bottom) boxes found by looking for the pieces on the grey
CELLS = {
    "run1": (40, 60, 255, 285), "run2": (276, 50, 510, 285), "run3": (540, 44, 756, 288),
    "run4": (768, 68, 992, 288), "run5": (1022, 40, 1260, 290),
    "rise": (290, 364, 515, 590), "apex": (538, 318, 780, 548), "fall": (796, 368, 1020, 596),
    "idle": (545, 785, 760, 980),
}
H = 46


def cut(box):
    sheet = np.array(Image.open(SRC).convert("RGB")).astype(int)
    l, t, r, b = box
    a = sheet[t:b, l:r]
    bg = np.array([79, 82, 96])
    fg = np.abs(a - bg).sum(2) > 40
    # the soft ground shadow is a paler navy than the outline: drop it near the feet
    lum = a.sum(2) / 3
    h = a.shape[0]
    shadow = (np.arange(h)[:, None] > h * 0.74) & (lum > 22) & (lum < 72) & (a[..., 2] > a[..., 0] + 12) & (a[..., 0] < 80) & (a[..., 1] < 90)
    fg &= ~shadow
    lab, n = ndimage.label(ndimage.binary_dilation(fg, iterations=3))
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg &= lab == (1 + int(np.argmax(sizes)))
    rgba = np.zeros(a.shape[:2] + (4,), dtype="uint8")
    rgba[..., :3] = a
    rgba[..., 3] = np.where(fg, 255, 0)
    return trim(Image.fromarray(rgba))


def frames():
    out = {}
    scale = None
    for name, box in CELLS.items():
        im = cut(box)
        if scale is None:
            scale = H / im.height                       # one scale for all poses, so the hero keeps its size
        w, h = max(1, round(im.width * scale)), max(1, round(im.height * scale))
        out[name] = put(old.W, old.H, resize(im, w, h), 0, 0)
    prev = old.frames()
    out["hurt"], out["cheer"] = prev["hurt"], prev["cheer"]
    return out


NAMES = ["idle", "run1", "run2", "run3", "run4", "run5", "rise", "apex", "fall", "hurt", "cheer"]

if __name__ == "__main__":
    from pixelkit import preview
    f = frames()
    preview([f[n] for n in NAMES], "/tmp/g/od/hero2.png", scale=4)
