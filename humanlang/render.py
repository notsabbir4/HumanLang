"""Turns a finished page (from designrun.py) into one self-contained web page (HTML, no scripts, no downloads)."""
import html
import math

SIZE_PX = {"tiny": 12, "small": 14, "normal": 18, "big": 30, "huge": 52}
FONTS = {
    "normal": "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif",
    "serif": "Georgia,'Times New Roman',serif",
    "monospace": "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
    "mono": "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
    "rounded": "'Trebuchet MS','Comic Sans MS',system-ui,sans-serif",
}
CSS = """*{box-sizing:border-box}
body{margin:0;font:18px/1.5 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;color:#1d2433;background:#fff}
.hl-page{min-height:100vh;display:flex;flex-direction:column;align-items:flex-start;gap:12px;padding:24px;margin:0 auto}
.hl-box{display:flex;flex-direction:column;align-items:flex-start;gap:8px}
.hl-row{display:flex;flex-direction:row;flex-wrap:wrap;align-items:center;gap:8px}
.hl-text{margin:0}
.hl-box[style*="grid-template-columns"]>button.hl,.hl-row[style*="grid-template-columns"]>button.hl{width:100%}
h1.hl-text{font-size:2.2rem;line-height:1.2}
button.hl{font:inherit;cursor:pointer;padding:.45em 1em;border:1px solid #8a93a6;background:#eef0f4;border-radius:8px;color:inherit}
button.hl:hover{filter:brightness(.95)}
input.hl{font:inherit;padding:.4em .6em;border:1px solid #8a93a6;border-radius:8px;min-width:12em;color:inherit;background:#fff}
svg.hl{display:block;max-width:100%;height:auto}
"""


def esc(x):
    return html.escape(str(x), quote=True)


def num(x):
    return str(int(x)) if x == int(x) else f"{x:.3f}".rstrip("0").rstrip(".")


def size_px(v):
    return SIZE_PX[v] if isinstance(v, str) else v


def style_for(kind, p, in_page=False):
    """The CSS for a layout element, from its properties."""
    css = []
    if "background" in p:
        css.append(f"background:{p['background']}" if p["background"] != "none" else "background:transparent")
    if "colour" in p:
        css.append(f"color:{p['colour']}")
    if "padding" in p:
        css.append(f"padding:{num(p['padding'])}px")
    if "space between" in p:
        css.append(f"gap:{num(p['space between'])}px")
    if "columns" in p:
        css.append(f"display:grid;grid-template-columns:repeat({int(p['columns'])},1fr);align-items:stretch")
    if "border" in p or "border colour" in p:
        css.append(f"border:{num(p.get('border', 1))}px solid {p.get('border colour', '#8a93a6')}")
    if "rounded" in p:
        r = 10 if p["rounded"] is True else p["rounded"]
        css.append(f"border-radius:{num(r)}px")
    if "width" in p:
        css.append("width:100%" if p["width"] == "full" else f"width:{num(p['width'])}px" if not in_page else f"max-width:{num(p['width'])}px;width:100%")
    if "height" in p:
        css.append("height:100%" if p["height"] == "full" else f"height:{num(p['height'])}px")
    if "size" in p:
        css.append(f"font-size:{num(size_px(p['size']))}px")
    if p.get("bold"):
        css.append("font-weight:700")
    if p.get("italic"):
        css.append("font-style:italic")
    if p.get("underlined"):
        css.append("text-decoration:underline")
    if "font" in p:
        css.append(f"font-family:{FONTS[p['font']]}")
    align = p.get("align", "center" if p.get("centered") else None)
    if align:
        align = "center" if align == "centre" else align
        items = {"left": "flex-start", "center": "center", "right": "flex-end"}[align]
        css.append(f"align-items:{items};text-align:{align}")
        if kind in ("text", "heading") and "width" not in p:
            css.append("align-self:stretch")
        if kind == "row":
            css.append(f"justify-content:{items}")
    if p.get("shadow"):
        css.append("box-shadow:0 4px 14px rgba(0,0,0,.25)")
    if p.get("centered") and kind in ("box", "row", "drawing"):
        css.append("margin-left:auto;margin-right:auto")
    return ";".join(css)


# ---- drawings ------------------------------------------------------------------------
def shape_svg(n):
    """(svg text, right edge, bottom edge) for a shape placed in a drawing."""
    k, p = n["kind"], n.get("props", {})
    fill = p.get("colour", "#000000")
    border = ""
    if "border" in p or "border colour" in p:
        border = f' stroke="{p.get("border colour", "#000000")}" stroke-width="{num(p.get("border", 1))}"'
    stroke_w = p.get("border", 1 if "border colour" in p else 0)
    pad = stroke_w / 2
    fill_attr = f' fill="{fill}"' if fill != "none" else ' fill="none"'
    if k == "circle":
        x, y = n["at"]
        r = p["radius"]
        return f'<circle cx="{num(x)}" cy="{num(y)}" r="{num(r)}"{fill_attr}{border}/>', x + r + pad, y + r + pad
    if k == "oval":
        x, y = n["at"]
        w, h = p["width"], p["height"]
        return (f'<ellipse cx="{num(x)}" cy="{num(y)}" rx="{num(w / 2)}" ry="{num(h / 2)}"{fill_attr}{border}/>',
                x + w / 2 + pad, y + h / 2 + pad)
    if k in ("rectangle", "square"):
        x, y = n["at"]
        w = p["width"]
        h = p["height"] if k == "rectangle" else w
        rx = ""
        if "rounded" in p:
            rx = f' rx="{num(10 if p["rounded"] is True else p["rounded"])}"'
        return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"{rx}{fill_attr}{border}/>',
                x + w + pad, y + h + pad)
    if k == "triangle":
        x, y = n["at"]
        w, h = p["width"], p["height"]
        pts = f"{num(x + w / 2)},{num(y)} {num(x + w)},{num(y + h)} {num(x)},{num(y + h)}"
        return f'<polygon points="{pts}"{fill_attr}{border}/>', x + w + pad, y + h + pad
    if k == "polygon":
        pts = " ".join(f"{num(x)},{num(y)}" for x, y in n["points"])
        return (f'<polygon points="{pts}"{fill_attr}{border}/>',
                max(x for x, _ in n["points"]) + pad, max(y for _, y in n["points"]) + pad)
    if k == "line":
        (x1, y1), (x2, y2) = n["points"]
        t = p.get("thickness", 2)
        return (f'<line x1="{num(x1)}" y1="{num(y1)}" x2="{num(x2)}" y2="{num(y2)}" stroke="{p.get("colour", "#000000")}" '
                f'stroke-width="{num(t)}" stroke-linecap="round"/>', max(x1, x2) + t / 2, max(y1, y2) + t / 2)
    if k == "text":
        x, y = n["at"]
        size = size_px(p.get("size", "normal"))
        weight = ' font-weight="700"' if p.get("bold") else ""
        style = ' font-style="italic"' if p.get("italic") else ""
        deco = ' text-decoration="underline"' if p.get("underlined") else ""
        font = f' font-family="{esc(FONTS[p["font"]])}"' if "font" in p else ""
        colour = p.get("colour", "currentColor")
        text = n.get("text", "")
        return (f'<text x="{num(x)}" y="{num(y)}" font-size="{num(size)}" fill="{colour}" dominant-baseline="hanging"'
                f'{weight}{style}{deco}{font}>{esc(text)}</text>', x + len(text) * size * 0.62, y + size * 1.25)
    if k == "pixel art":
        x, y = n["at"]
        body, w, h = pixel_rects(n)
        return f'<g transform="translate({num(x)},{num(y)})" shape-rendering="crispEdges">{body}</g>', x + w, y + h
    raise ValueError(k)


def pixel_rects(n):
    ps = n.get("props", {}).get("pixel size", 10)
    legend, rows = n["legend"], n["rows"]
    out = []
    for r, row in enumerate(rows):
        c = 0
        while c < len(row):
            colour = legend.get(row[c])
            if colour is None:
                c += 1
                continue
            end = c
            while end + 1 < len(row) and legend.get(row[end + 1]) == colour:
                end += 1
            out.append(f'<rect x="{num(c * ps)}" y="{num(r * ps)}" width="{num((end - c + 1) * ps)}" height="{num(ps)}" fill="{colour}"/>')
            c = end + 1
    return "".join(out), len(rows[0]) * ps, len(rows) * ps


def drawing_svg(children, width=None, height=None, name=None, style="", background=None):
    parts, right, bottom = [], 0, 0
    for n in children:
        svg, x2, y2 = shape_svg(n)
        parts.append(svg)
        right, bottom = max(right, x2), max(bottom, y2)
    w = width if width is not None else math.ceil(right) + 1
    h = height if height is not None else math.ceil(bottom) + 1
    bg = f'<rect width="100%" height="100%" fill="{background}"/>' if background and background != "none" else ""
    idattr = f' id="{esc(name)}"' if name else ""
    return (f'<svg class="hl"{idattr} xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" '
            f'viewBox="0 0 {num(w)} {num(h)}" shape-rendering="auto"{(" style=" + chr(34) + style + chr(34)) if style else ""}>{bg}{"".join(parts)}</svg>')


def standalone_pixel(n):
    body, w, h = pixel_rects(n)
    idattr = f' id="{esc(n["name"])}"' if n.get("name") else ""
    return (f'<svg class="hl"{idattr} xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" '
            f'viewBox="0 0 {num(w)} {num(h)}" shape-rendering="crispEdges">{body}</svg>')


# ---- layout ---------------------------------------------------------------------------
def is_placed(n):
    return "at" in n or n["kind"] in ("line", "polygon")


def render_children(children):
    out, group = [], []

    def flush():
        if group:
            out.append(drawing_svg(list(group)))
            group.clear()

    for n in children:
        if is_placed(n):
            group.append(n)
        else:
            flush()
            out.append(render(n))
    flush()
    return "".join(out)


def render(n):
    k, p = n["kind"], n.get("props", {})
    idattr = f' id="{esc(n["name"])}"' if n.get("name") else ""
    if k in ("box", "row"):
        st = style_for(k, p)
        return f'<div class="hl-{k}"{idattr}{(" style=" + chr(34) + st + chr(34)) if st else ""}>{render_children(n["children"])}</div>'
    if k in ("text", "heading"):
        st = style_for(k, p)
        tag = "h1" if k == "heading" else "p"
        return f'<{tag} class="hl-text"{idattr}{(" style=" + chr(34) + st + chr(34)) if st else ""}>{esc(n.get("text", ""))}</{tag}>'
    if k == "button":
        st = style_for(k, p)
        return f'<button type="button" class="hl"{idattr}{(" style=" + chr(34) + st + chr(34)) if st else ""}>{esc(n.get("text", ""))}</button>'
    if k == "input":
        st = style_for(k, p)
        hint = esc(p.get("hint", ""))
        return (f'<input type="text" class="hl"{idattr} placeholder="{hint}" aria-label="{hint or "text box"}"'
                f'{(" style=" + chr(34) + st + chr(34)) if st else ""}>')
    if k == "drawing":
        st = []
        if "border" in p or "border colour" in p:
            st.append(f"border:{num(p.get('border', 1))}px solid {p.get('border colour', '#8a93a6')}")
        if "rounded" in p:
            st.append(f"border-radius:{num(10 if p['rounded'] is True else p['rounded'])}px")
        if p.get("shadow"):
            st.append("box-shadow:0 4px 14px rgba(0,0,0,.25)")
        if p.get("centered"):
            st.append("margin-left:auto;margin-right:auto")
        return drawing_svg(n["children"], p.get("width", 300) if p.get("width") != "full" else 300, p.get("height", 200) if p.get("height") != "full" else 200,
                           n.get("name"), ";".join(st), p.get("background"))
    if k == "pixel art":
        return standalone_pixel(n)
    raise ValueError(k)


def to_html(page):
    p = page.get("props", {})
    title = page.get("title") or "HumanLang page"
    body_css = []
    if "background" in p and p["background"] != "none":
        body_css.append(f"background:{p['background']}")
    if "colour" in p:
        body_css.append(f"color:{p['colour']}")
    if "font" in p:
        body_css.append(f"font-family:{FONTS[p['font']]}")
    page_css = []
    if "padding" in p:
        page_css.append(f"padding:{num(p['padding'])}px")
    if "space between" in p:
        page_css.append(f"gap:{num(p['space between'])}px")
    if "width" in p and p["width"] != "full":
        page_css.append(f"max-width:{num(p['width'])}px;width:100%")
    align = p.get("align", "center" if p.get("centered") else None)
    if align:
        align = "center" if align == "centre" else align
        page_css.append(f"align-items:{ {'left': 'flex-start', 'center': 'center', 'right': 'flex-end'}[align] };text-align:{align}")
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n"
            f"<body{(' style=' + chr(34) + ';'.join(body_css) + chr(34)) if body_css else ''}>\n"
            f"<main class=\"hl-page\"{(' style=' + chr(34) + ';'.join(page_css) + chr(34)) if page_css else ''}>"
            f"{render_children(page['children'])}</main>\n</body>\n</html>\n")
