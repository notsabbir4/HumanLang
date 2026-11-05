"""Running a design: `show a page` and `put ...` build a tree of plain data (dicts); render.py draws it."""
import math

from .design import (CONTAINERS, SHAPES, ALLOWED, colour_problem, resolve_colour)

MAX_ELEMENTS = 20000
MAX_TEXT = 5000
MAX_NUMBER = 100000
NOT_NEGATIVE = ("radius", "width", "height", "thickness", "border", "padding", "space between", "rounded", "columns")
DRAWABLE = SHAPES + ("text",)


class DesignRun:
    """Mixed into the Interpreter."""

    designs = None  # the pages shown so far, newest last (set in Interpreter.__init__)
    on_design = None  # a function the host sets; called with each finished page

    def design_init(self):
        self.designs = []
        self.design_stack = []
        self.design_names = set()
        self.design_count = 0

    # -- values --------------------------------------------------------------------
    def dnumber(self, expr, env, what):
        v = self.ev(expr, env)
        if isinstance(v, bool) or not isinstance(v, (int, float)) and not hasattr(v, "as_tuple"):
            raise self.err(f'{what} needs a number, but got {self.show(v)}.')
        x = float(v)
        if math.isnan(x) or abs(x) > MAX_NUMBER:
            raise self.err(f"{what} is too big: numbers on a page stay between -{MAX_NUMBER} and {MAX_NUMBER}.")
        return int(x) if x == int(x) else round(x, 3)

    def dcolour(self, text):
        found = resolve_colour(text)
        if found is None:
            msg, hint = colour_problem(text)
            raise self.err(msg, hint)
        return found

    def dprops(self, props, env):
        out = {}
        for name, spec in props:
            kind = spec[0]
            if kind == "colour":
                out[name] = spec[1]
            elif kind == "colourexpr":
                v = self.ev(spec[1], env)
                out[name] = "none" if str(v).lower() in ("nothing", "none", "transparent") else self.dcolour(self.fmt(v))
            elif kind == "colourvar":
                holder = env.find(spec[1])
                if holder is None:  # not a variable either: it was a mistyped colour
                    msg, hint = colour_problem(spec[1])
                    raise self.err(msg, hint)
                v = holder.vars[spec[1]]
                out[name] = "none" if str(v).lower() in ("nothing", "none", "transparent") else self.dcolour(self.fmt(v))
            elif kind == "num":
                n = self.dnumber(spec[1], env, f'"{name}"')
                if name in NOT_NEGATIVE and n < 0:
                    raise self.err(f'"{name}" can\'t be negative, but got {n}.')
                if name == "columns" and (n < 1 or n != int(n) or n > 100):
                    raise self.err(f'"columns" must be a whole number from 1 to 100, but got {n}.')
                if name in ("pixel size", "size") and n <= 0:
                    raise self.err(f'"{name}" must be more than 0, but got {n}.')
                out[name] = n
            elif kind == "text":
                out[name] = self.limited(self.fmt(self.ev(spec[1], env)))
            elif kind == "flag":
                out[name] = True if spec[1] is None else self.dnumber(spec[1], env, f'"{name}"')
            else:
                out[name] = spec[1]
        return out

    def limited(self, text):
        if len(text) > MAX_TEXT:
            raise self.err(f"A piece of text on a page can have at most {MAX_TEXT} letters.")
        return text

    # -- statements ------------------------------------------------------------------
    def x_page(self, s, env):
        _, line, title, props, body = s
        if self.design_stack:
            raise self.err("A page can't be inside another page.")
        page = {"kind": "page", "title": None, "props": {}, "children": []}
        if title is not None:
            page["title"] = self.limited(self.fmt(self.ev(title, env)))
        page["props"] = self.dprops(props, env)
        self.design_stack.append(page)
        self.design_names, self.design_count = set(), 0
        try:
            self.exec_block(body, env)
        finally:
            self.design_stack.pop()
        self.designs.append(page)
        if self.on_design:
            self.on_design(page)

    def x_put(self, s, env):
        _, line, kind, content, name, pos, points, props, body, extra = s
        if not self.design_stack:
            raise self.err('"put" only works while a page is being built.',
                           "Put it inside: show a page ... (not inside a function that runs later).")
        parent = self.design_stack[-1]
        if parent["kind"] == "drawing" and kind not in DRAWABLE:
            raise self.err(f"A drawing can only hold shapes, pixel art and text placed at a spot, not a {kind}.")
        self.design_count += 1
        if self.design_count > MAX_ELEMENTS:
            raise self.err(f"This page has more than {MAX_ELEMENTS} things on it, so I stopped.")
        node = {"kind": kind}
        if content is not None:
            node["text"] = self.limited(self.fmt(self.ev(content, env)))
        if name is not None:
            if name in self.design_names:
                raise self.err(f'Two things on this page are called "{name}".', "Give each one its own name.")
            self.design_names.add(name)
            node["name"] = name
        if pos is not None:
            node["at"] = (self.dnumber(pos[0], env, "The spot's first number (across)"),
                          self.dnumber(pos[1], env, "The spot's second number (down)"))
        if points:
            node["points"] = [(self.dnumber(x, env, "A corner's first number"), self.dnumber(y, env, "A corner's second number"))
                              for x, y in points]
        node["props"] = self.dprops(props, env)
        if extra is not None:
            node["rows"], node["legend"] = extra["rows"], extra["legend"]
        if kind in CONTAINERS:
            node["children"] = []
        if kind == "text" and "at" in node and parent["kind"] not in ("drawing", "page", "box", "row"):
            pass
        parent["children"].append(node)
        if body:
            self.design_stack.append(node)
            try:
                self.exec_block(body, env)
            finally:
                self.design_stack.pop()
