"""Small helpers that turn pictures into HumanLang sprites (pixel size 1).

The artwork of HumanLang Odyssey is converted from the project's own pictures (the HL mascot) or drawn here with shapes
and shading, then written out as `make a sprite` blocks. The game itself is plain HumanLang: this tool only makes the
rows of coloured squares, the way a person would type them, so nobody has to type 50,000 letters by hand.
"""
import string

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

CHARS = string.ascii_letters + string.digits + "@%&$*+=~^!?:;,<>|/_-"   # never: . (clear), a quote, a backslash, a hash
ALPHA_CUT = 118


def load(path):
    return Image.open(path).convert("RGBA")


def harden(im, cut=200):
    """Drop the soft, see-through pixels (ground shadows, glows): the character itself is solid."""
    a = np.array(im)
    a[..., 3] = np.where(a[..., 3] >= cut, 255, 0)
    return Image.fromarray(a)


def main_part(im, grow=1):
    """Keep only the biggest connected piece (the character), dropping floating sparkles, hearts and speed lines."""
    a = np.array(im)[..., 3] > 24
    lab, n = ndimage.label(ndimage.binary_dilation(a, iterations=grow))
    if n <= 1:
        return im
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = lab == (1 + int(np.argmax(sizes)))
    arr = np.array(im)
    arr[..., 3] = np.where(keep & a, arr[..., 3], 0)
    return Image.fromarray(arr)


def resize(im, w, h):
    return im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


def put(canvas_w, canvas_h, im, dx=0, dy=0, anchor="bottom"):
    """Place the picture on a transparent canvas: centred sideways, resting on the bottom (feet)."""
    c = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    x = (canvas_w - im.width) // 2 + dx
    y = (canvas_h - im.height) + dy if anchor == "bottom" else (canvas_h - im.height) // 2 + dy
    c.alpha_composite(im, (x, y))
    return c


def trim(im):
    box = im.getbbox()
    return im.crop(box) if box else im


def palette_of(frames, colours):
    """One shared palette for all frames (so the animation does not flicker): median cut over every solid pixel."""
    px = []
    for f in frames:
        a = np.array(f)
        px.append(a[a[..., 3] >= ALPHA_CUT][:, :3])
    px = np.concatenate(px)
    strip = Image.fromarray(px.reshape(1, -1, 3).astype("uint8"))
    q = strip.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[: 3 * colours]
    cols = [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]
    used = sorted(set(q.getdata()))
    return [cols[i] for i in used if i < len(cols)]


def remap(frame, pal):
    """Every solid pixel becomes the nearest palette colour; everything else is clear (None)."""
    a = np.array(frame)
    p = np.array(pal, dtype=int)
    out = np.full(a.shape[:2], -1, dtype=int)
    solid = a[..., 3] >= ALPHA_CUT
    d = ((a[..., :3][:, :, None, :].astype(int) - p[None, None, :, :]) ** 2).sum(-1)
    out[solid] = d.argmin(-1)[solid]
    return out


class Sheet:
    """Collects palettes and writes sprites as HumanLang source."""

    def __init__(self):
        self.parts = []

    def sprite(self, name, frames, colours=24, note=None, pal=None):
        """frames: list of RGBA images, all the same size."""
        if not isinstance(frames, (list, tuple)):
            frames = [frames]
        w, h = frames[0].size
        assert all(f.size == (w, h) for f in frames), name + ": frames differ in size"
        pal = pal or palette_of(frames, colours)
        grids = [remap(f, pal) for f in frames]
        assert len(pal) <= len(CHARS), name + ": too many colours"
        head = f"make a sprite called {name} with pixel size 1"
        if len(frames) > 1:
            head += f" and {len(frames)} frames"
        lines = []
        if note:
            lines.append(f"note: {note}")
        lines.append(head)
        for i, c in enumerate(pal):
            lines.append(f'    where "{CHARS[i]}" is "#{c[0]:02X}{c[1]:02X}{c[2]:02X}"')
        for g in grids:
            for row in g:
                lines.append('    "' + "".join("." if v < 0 else CHARS[v] for v in row) + '"')
        self.parts.append("\n".join(lines))
        return pal

    def text(self):
        return "\n\n".join(self.parts) + "\n"


def preview(frames, path, scale=6, bg=(190, 205, 225)):
    w = sum(f.width for f in frames) + 4 * (len(frames) + 1)
    h = max(f.height for f in frames) + 8
    im = Image.new("RGB", (w, h), bg)
    x = 4
    for f in frames:
        im.paste(f, (x, 4), f)
        x += f.width + 4
    im.resize((w * scale, h * scale), Image.NEAREST).save(path)
