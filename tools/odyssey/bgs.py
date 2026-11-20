"""The two backgrounds, from the pictures assets_src/bg_meadow.png and bg_snow.png, as 600 x 224 pixel-size-1 sprites.
The ground line of each picture is placed at y = 224, where the tiles of the level start. The snowy picture had two
floating snow blocks painted into it; they are painted out, because a background must never look like something to stand on."""
import os
import numpy as np
from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), "assets_src")
W, H = 600, 224
SCALE = W / 1672


def _crop(path, ground_y, fix=None):
    im = Image.open(os.path.join(SRC, path)).convert("RGB")
    if fix:
        a = np.array(im)
        fix(a)
        im = Image.fromarray(a)
    top = ground_y - round(H / SCALE)
    im = im.crop((0, top, 1672, ground_y))
    return im.resize((W, H), Image.LANCZOS).convert("RGBA")


def _unblock(a):
    """Paint out the two floating snow blocks (rows 688-780) with the clean mountain foot beside them."""
    y0, y1 = 686, 782
    a[y0:y1, 288:504] = a[y0:y1, 504:720]
    patch = a[y0:y1, 504:720]
    a[y0:y1, 1316:1516] = patch[:, :200]


def meadow():
    return _crop("bg_meadow.png", 825)


def snow():
    return _crop("bg_snow.png", 805, _unblock)


if __name__ == "__main__":
    meadow().save("/tmp/g/od/bg_m.png")
    snow().save("/tmp/g/od/bg_s.png")
