"""Design: describing a page (buttons, text, boxes, drawings, pixel art) in plain words.

    show a page titled "Hello"
        put a text "Welcome" with size big
        put a button "Click me" with background green
        put a circle at 50, 80 with radius 20 and colour white

This file knows how to READ that (the Parser mixin) and how to turn colour words into colours.
designrun.py runs it, and render.py turns the result into a web page.
"""
from .colours import CSS
from .errors import suggest

# ---- what can be put on a page ---------------------------------------------------
CONTAINERS = ("page", "box", "row", "drawing")
SHAPES = ("circle", "oval", "rectangle", "square", "triangle", "line", "polygon", "pixel art")
ALIASES = {"column": "box", "heading": "heading", "title": "heading", "ellipse": "oval", "pixelart": "pixel art"}
KINDS = ["box", "row", "text", "heading", "button", "input", "drawing",
         "circle", "oval", "rectangle", "square", "triangle", "line", "polygon", "pixel art"]
NEEDS_TEXT = ("text", "heading", "button")  # these need words to show

# ---- properties: "with background red, padding 10" ---------------------------------
#   colour: colour words   number: a calculation   size: small/big/... or a number   choice: one of some words
#   flag: just the word (some take an optional number)   dim: a number or "full"   text: a piece of text
PROPS = {
    "background": "colour", "colour": "colour", "color": "colour",
    "border colour": "colour", "border color": "colour",
    "border": "number", "padding": "number", "space between": "number", "columns": "number",
    "width": "dim", "height": "dim", "radius": "number", "thickness": "number", "pixel size": "number",
    "rounded": "flag", "bold": "flag", "italic": "flag", "underlined": "flag", "centered": "flag", "centred": "flag",
    "shadow": "flag", "size": "size", "align": "choice", "font": "choice", "hint": "text",
}
CHOICES = {"align": ("left", "center", "centre", "right"), "font": ("normal", "serif", "monospace", "mono", "rounded")}
SIZES = ("tiny", "small", "normal", "big", "huge")
CANON = {"color": "colour", "border color": "border colour", "centred": "centered"}

_TEXTY = ("colour", "size", "bold", "italic", "underlined", "align", "centered", "font")
_BOXY = ("background", "border", "border colour", "rounded", "padding", "width", "height", "shadow")
_LAYOUT = ("colour", "space between", "align", "centered", "font", "columns")
ALLOWED = {
    "page": ("background", "colour", "padding", "space between", "align", "centered", "font", "width"),
    "box": _BOXY + _LAYOUT,
    "row": _BOXY + _LAYOUT,
    "text": _TEXTY + ("background", "padding", "rounded", "width"),
    "heading": _TEXTY + ("background", "padding", "rounded", "width"),
    "button": _TEXTY + _BOXY,
    "input": ("hint", "width", "size", "background", "colour", "border", "border colour", "rounded", "padding", "font"),
    "drawing": ("width", "height", "background", "border", "border colour", "rounded", "shadow", "centered"),
    "circle": ("radius", "colour", "border", "border colour"),
    "oval": ("width", "height", "colour", "border", "border colour"),
    "rectangle": ("width", "height", "colour", "border", "border colour", "rounded"),
    "square": ("width", "colour", "border", "border colour", "rounded"),
    "triangle": ("width", "height", "colour", "border", "border colour"),
    "line": ("colour", "thickness"),
    "polygon": ("colour", "border", "border colour"),
    "pixel art": ("pixel size",),
}
TEXT_AT = ("colour", "size", "bold", "italic", "underlined", "font")  # a text placed at a spot in a drawing
NEEDS = {"circle": ("radius",), "oval": ("width", "height"), "rectangle": ("width", "height"),
         "square": ("width",), "triangle": ("width", "height")}
EXAMPLES = {
    "page": 'show a page titled "Hello"',
    "put": 'put a button "Click me" with background green',
    "circle": "put a circle at 50, 80 with radius 20 and colour red",
    "oval": "put an oval at 50, 80 with width 60 and height 30",
    "rectangle": "put a rectangle at 10, 10 with width 80 and height 40",
    "square": "put a square at 10, 10 with width 40",
    "triangle": "put a triangle at 10, 10 with width 40 and height 40",
    "line": "put a line from 0, 0 to 100, 50 with colour red",
    "polygon": "put a polygon from 10, 10 to 60, 10 to 35, 50",
    "pixel art": 'put pixel art at 10, 10 with pixel size 8',
    "text": 'put a text "Hello" with size big',
    "heading": 'put a heading "My page"',
    "button": 'put a button "Click me"',
    "input": 'put an input with hint "Your name"',
}

# ---- colours ----------------------------------------------------------------------
EXTRA_COLOURS = {"skin": "#f1c27d", "brightred": "#ff1a1a"}
COLOUR_NAMES = sorted(set(CSS) | set(EXTRA_COLOURS))


def _mix(hex_colour, target, amount):
    a = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(target[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


def resolve_colour(text):
    """Colour words ("dark blue", "red", "#ff8800") as #rrggbb, or None when they are not a colour."""
    text = " ".join(str(text).lower().replace("-", " ").replace("_", " ").split())
    if not text:
        return None
    if text.startswith("#"):
        digits = text[1:]
        if len(digits) in (3, 6) and all(c in "0123456789abcdef" for c in digits):
            if len(digits) == 3:
                digits = "".join(c * 2 for c in digits)
            return "#" + digits
        return None
    words = text.split()
    joined = "".join(words)
    if joined in EXTRA_COLOURS:
        return EXTRA_COLOURS[joined]
    if joined in CSS:
        return CSS[joined]
    if words[0] in ("dark", "light", "pale", "bright") and len(words) > 1:
        base = resolve_colour(" ".join(words[1:]))
        if base:
            return _mix(base, "#000000" if words[0] == "dark" else "#ffffff", 0.35 if words[0] != "bright" else 0.0)
    return None


def colour_problem(text):
    """The error text for something that is not a colour."""
    first = " ".join(str(text).lower().split())
    hint = suggest(first.replace(" ", ""), COLOUR_NAMES) or "Use a colour name like red, dark blue or sky blue, or a code like \"#ff8800\"."
    return f'I don\'t know the colour "{text}".', hint


# ---- reading it (mixed into the Parser) ---------------------------------------------
class DesignParser:
    in_design = 0
    design_content = False  # true while reading the words of a text or button: "put a button key with width 60"

    def prop_word(self, k):
        """Is the token k places ahead the start of a property (background, width, ...)?"""
        t = self.peek(k)
        return t is not None and t.kind == "WORD" and t.value in {p.split()[0] for p in PROPS}

    def st_page(self):
        line, lvl = self.lineno, self.level
        self.example = EXAMPLES["page"]
        if self.in_design:
            self.fail("A page can't be inside another page", hint="Put the second page after the first one, not inside it.")
        self.expect("a")
        self.expect("page")
        self.design_content = True
        try:
            title = self.arith() if self.accept("titled") else None
            props = self.design_props("page") if self.accept("with") else []
            self.end()
        finally:
            self.design_content = False
        self.in_design += 1
        try:
            body = self.body(lvl)
        finally:
            self.in_design -= 1
        return ("page", line, title, props, body)

    def comma(self, what):
        t = self.peek()
        if t is not None and t.kind == "OP" and t.value == ",":
            self.i += 1
            return
        self.fail(f"I expected a comma here, between the two numbers of {what}")

    def point(self, what):
        x = self.arith()
        self.comma(what)
        return (x, self.arith())

    def st_put(self):
        self.design_content = True
        try:
            return self.st_put_inner()
        finally:
            self.design_content = False

    def st_put_inner(self):
        line, lvl = self.lineno, self.level
        if not (self.accept("a") or self.accept("an")):
            self.accept("some")
        t = self.peek()
        if t is None or t.kind != "WORD":
            self.example = EXAMPLES["put"]
            self.fail("I expected what to put on the page here, like a button or a text")
        if t.value == "pixel" and self.word("art", 1):
            kind, self.i = "pixel art", self.i + 2
        else:
            kind = ALIASES.get(t.value, t.value)
            if kind not in KINDS:
                self.example = EXAMPLES["put"]
                self.fail(f'I don\'t know how to put "{t.value}" on a page',
                          hint=(suggest(t.value, KINDS + ["column"]) or "") + ("  " if suggest(t.value, KINDS) else "")
                          + "You can put: " + ", ".join(KINDS) + ".")
            self.i += 1
        self.example = EXAMPLES.get(kind, EXAMPLES["put"])

        content = name = pos = None
        points, props = [], []
        nxt = self.peek()
        if nxt is not None and not (nxt.kind == "WORD" and nxt.value in ("called", "at", "from", "with")):
            if kind in NEEDS_TEXT:
                content = self.arith()
            else:
                self.fail(f'A {kind} doesn\'t have words of its own, so I didn\'t expect "{self.show(nxt)}" here')
        elif kind in NEEDS_TEXT:
            self.fail(f"A {kind} needs the words to show, in quotes")
        seen = set()
        first_words = {p.split()[0] for p in PROPS}
        while self.peek() is not None:
            t = self.peek()
            if t.kind == "OP" and t.value == ",":  # "called screen, size big": a comma may join the parts
                self.i += 1
                continue
            if t.kind != "WORD" or t.value not in ("called", "at", "from", "with") + tuple(first_words):
                break
            w = "with" if t.value in first_words else t.value
            if w in seen:
                self.fail(f'"{t.value}" is there twice')
            seen.add(w)
            if w != "with" or t.value == "with":
                self.i += 1
            if w == "called":
                name = self.name()
            elif w == "at":
                if kind not in SHAPES and kind != "text" or kind in ("line", "polygon"):
                    self.fail(f'A {kind} can\'t be placed "at" a spot',
                              hint="Only drawings can: circle, oval, rectangle, square, triangle, pixel art, and a text. "
                                   "A line or polygon uses from ... to ..." if kind in ("line", "polygon") else
                                   "Only shapes, pixel art and a text can be placed at a spot.")
                pos = self.point("the spot")
            elif w == "from":
                if kind not in ("line", "polygon"):
                    self.fail(f'A {kind} doesn\'t use "from ... to ..."', hint="That is for a line or a polygon.")
                points.append(self.point("a corner"))
                while self.accept("to"):
                    points.append(self.point("a corner"))
            else:
                props = self.design_props(kind, positioned=pos is not None)
        self.end()
        if kind == "line" and len(points) != 2:
            self.fail("A line needs a start and an end")
        if kind == "polygon" and len(points) < 3:
            self.fail("A polygon needs at least three corners")
        if kind in SHAPES and kind not in ("line", "polygon", "pixel art") and pos is None:
            self.fail(f"A {kind} needs a spot: at X, Y")
        if kind == "text" and pos is not None:
            pass
        given = {p[0] for p in props}
        for need in NEEDS.get(kind, ()):
            if need not in given:
                self.fail(f"A {kind} needs a {need}", hint=f"Example: {EXAMPLES[kind]}")
        extra, body = None, None
        self.design_content = False  # the lines indented below are ordinary statements again
        if kind == "pixel art":
            extra = self.pixel_rows(lvl)
        elif kind in CONTAINERS:
            body = self.design_body(lvl)
        return ("put", line, kind, content, name, pos, points, props, body, extra)

    def design_body(self, lvl):
        if self.pos < len(self.lines) and self.lines[self.pos].indent > lvl:
            self.in_design += 1
            try:
                return self.body(lvl)
            finally:
                self.in_design -= 1
        return []

    # -- properties ------------------------------------------------------------------
    def design_props(self, kind, positioned=False):
        allowed = ALLOWED[kind] if not (kind == "text" and positioned) else TEXT_AT
        props = []
        while True:
            t = self.peek()
            if t is None or t.kind != "WORD":
                self.fail("I expected a property here, like background or size" if not props
                          else "I expected another property after the comma")
            name = t.value
            if self.peek(1) is not None and self.peek(1).kind == "WORD" and f"{name} {self.peek(1).value}" in PROPS:
                name, self.i = f"{name} {self.peek(1).value}", self.i + 2
            elif name in PROPS:
                self.i += 1
            else:
                nice = sorted({CANON.get(p, p) for p in allowed})
                self.fail(f'A {kind} doesn\'t have "{name}"',
                          hint=(suggest(name, list(PROPS)) or "") + ("  " if suggest(name, list(PROPS)) else "")
                          + "A " + kind + " can have: " + ", ".join(nice) + ".")
            canon = CANON.get(name, name)
            if canon not in {CANON.get(p, p) for p in allowed}:
                nice = sorted({CANON.get(p, p) for p in allowed})
                self.fail(f'A {kind}{" placed at a spot" if positioned and kind == "text" else ""} doesn\'t have "{name}"',
                          hint="It can have: " + ", ".join(nice) + ".")
            props.append((canon, self.prop_value(canon)))
            t = self.peek()
            if t is not None and t.kind == "OP" and t.value == ",":
                self.i += 1
                self.accept("and")
                continue
            if self.accept("and"):
                continue
            break
        return props

    def colour_words(self, what):
        t = self.peek()
        if t is not None and t.kind == "STR":
            return ("colourexpr", self.arith())
        words = []
        while self.peek() is not None and self.peek().kind == "WORD" and self.peek().value != "and":
            words.append(self.peek().value)
            self.i += 1
        if not words:
            self.fail(f"I expected a colour after {what}, like red or dark blue")
        text = " ".join(words)
        if text in ("nothing", "none", "transparent"):
            return ("colour", "none")
        found = resolve_colour(text)
        if found is None:
            if len(words) == 1:  # maybe a variable that holds a colour: set c to "red", then colour c
                return ("colourvar", words[0])
            msg, hint = colour_problem(text)
            self.fail(msg, hint)
        return ("colour", found)

    def prop_value(self, name):
        kind = PROPS[name]
        if kind == "colour":
            return self.colour_words(name)
        if kind == "number":
            return ("num", self.arith())
        if kind == "text":
            return ("text", self.arith())
        if kind == "flag":
            t = self.peek()
            if name == "rounded" and t is not None and (t.kind == "NUM" or (t.kind == "OP" and t.value == "(")):
                return ("flag", self.arith())
            return ("flag", None)
        if kind == "dim":
            if self.accept("full"):
                return ("word", "full")
            return ("num", self.arith())
        if kind == "size":
            t = self.peek()
            if t is not None and t.kind == "WORD" and t.value in SIZES:
                self.i += 1
                return ("word", t.value)
            if t is None or not (t.kind == "NUM" or (t.kind == "OP" and t.value in ("(", "-")) or t.kind == "WORD"):
                self.fail(f'I expected a size here: {", ".join(SIZES)}, or a number')
            return ("num", self.arith())
        t = self.peek()  # choice
        options = CHOICES[name]
        if t is None or t.kind != "WORD" or t.value not in options:
            self.fail(f'"{name}" can be: {", ".join(options)}')
        self.i += 1
        return ("word", t.value)

    # -- pixel art ---------------------------------------------------------------------
    def pixel_rows(self, lvl, allow_sprites=False):
        rows, legend, first_row = [], {".": None, " ": None}, None
        if not (self.pos < len(self.lines) and self.lines[self.pos].indent > lvl):
            self.fail("Pixel art needs its rows, indented below it",
                      hint='Example:\nput pixel art at 10, 10 with pixel size 8\n    where "r" is red\n    "rr"\n    "rr"')
        while self.pos < len(self.lines) and self.lines[self.pos].indent > lvl:
            ln = self.lines[self.pos]
            if ln.indent != lvl + 1:
                self.lineno = ln.no
                self.fail("This line is indented too far", hint="Indent by exactly 4 spaces under the pixel art line.")
            self.pos += 1
            self.load(ln)
            if self.word("where"):
                self.i += 1
                while True:
                    t = self.peek()
                    if t is None or t.kind != "STR" or len(t.value) != 1 or t.value[0][0] != "t" or len(t.value[0][1]) != 1:
                        self.fail('After "where" write a one-letter text, then "is", then a colour, like: where "r" is red')
                    letter = t.value[0][1]
                    self.i += 1
                    self.expect("is")
                    if allow_sprites and self.words("the", "sprite"):
                        self.i += 2
                        legend[letter] = ["sprite", self.name()]
                    else:
                        spec = self.colour_words("is")
                        if spec[0] == "colourexpr" and spec[1][0] == "lit":  # a code in quotes, like "#ff8800"
                            found = resolve_colour(spec[1][1])
                            if found is None:
                                msg, hint = colour_problem(spec[1][1])
                                self.fail(msg, hint)
                            spec = ("colour", found)
                        if spec[0] != "colour":
                            self.fail("In pixel art, each letter is a colour name like red, or a code in quotes like \"#ff8800\"")
                        legend[letter] = None if spec[1] == "none" else spec[1]
                    t = self.peek()
                    if t is not None and t.kind == "OP" and t.value == ",":
                        self.i += 1
                        self.accept("and")
                        continue
                    if self.accept("and"):
                        continue
                    break
                self.end()
            else:
                t = self.peek()
                if len(self.toks) != 1 or t.kind != "STR" or any(p[0] != "t" for p in t.value):
                    self.fail('A pixel art row is a text like "..rr..", on a line by itself (no { } inside)',
                              hint='Or a line like: where "r" is red')
                text = "".join(p[1] for p in t.value)
                if first_row is None:
                    first_row = (len(text), ln.no)
                elif len(text) != first_row[0]:
                    self.fail(f"Every row of pixel art must be the same length: this one has {len(text)} letter{'s' if len(text) != 1 else ''}, "
                              f"but the first row (line {first_row[1]}) has {first_row[0]}")
                rows.append((ln.no, text))
        if not rows:
            self.fail("Pixel art needs at least one row")
        for no, text in rows:
            for ch in text:
                if ch not in legend:
                    self.lineno = no
                    self.fail(f'The letter "{ch}" in this pixel art row has no colour yet',
                              hint=f'Add a line like: where "{ch}" is red')
        return {"rows": [r for _n, r in rows], "legend": legend}
