"""Ready-made platformer physics: a BODY runs, jumps, falls and lands on solid tiles, so a game needs far less code.

    make a body called hero at 24, 150 with size 12 by 16
    ...
    every frame
        if key "left" is down
            make the body hero run left
        update the body hero on the map level with solid "#" and "B"
        draw the sprite hero at the body hero

This file READS those words (a Parser mixin) and RUNS them (an Interpreter mixin).
"""
import math

DEFAULTS = {"gravity": 0.45, "speed": 2.2, "jump": 5.8}
MAX_FALL = 12
ACTIONS = ("run left", "run right", "stop", "jump", "bounce")
EXAMPLES = {
    "body": "make a body called hero at 24, 150 with size 12 by 16",
    "do": "make the body hero run left   (also: run right, stop, jump, bounce)",
    "update": 'update the body hero on the map level with solid "#" and "B"',
    "move": "move the body hero to 24, 150",
}


class PhysicsParser:
    def body_name(self):
        self.expect("the")
        self.expect("body")
        return self.name()

    def make_body(self, line):
        self.example = EXAMPLES["body"]
        self.expect("called")
        name = self.name()
        opts = {}
        self.joiner()
        while self.peek() is not None:
            if self.word("at"):
                self.i += 1
                x = self.arith()
                self.comma("the spot")
                opts["at"] = (x, self.arith())
            elif self.word("size"):
                self.i += 1
                w = self.arith()
                self.expect("by")
                opts["size"] = (w, self.arith())
            elif self.peek().kind == "WORD" and self.peek().value in DEFAULTS:
                key = self.peek().value
                self.i += 1
                opts[key] = self.arith()
            else:
                break
            self.joiner()
        self.end()
        if "size" not in opts:
            self.fail("A body needs a size: with size 12 by 16")
        return ("body", line, name, opts)

    def st_bodydo(self):
        """make the body NAME run left / run right / stop / jump / bounce"""
        line = self.lineno
        self.example = EXAMPLES["do"]
        name = self.body_name()
        t = self.peek()
        word = t.value if t is not None and t.kind == "WORD" else None
        if word in ("jump", "bounce", "stop"):
            self.i += 1
            action = word
        elif word == "run":
            self.i += 1
            d = self.peek()
            if d is None or d.value not in ("left", "right"):
                self.fail('After "run" I expected "left" or "right"')
            self.i += 1
            action = "run " + d.value
        else:
            self.fail('I expected what the body should do: run left, run right, stop, jump or bounce')
        self.end()
        return ("bodydo", line, name, action)

    def st_update(self):
        line = self.lineno
        self.example = EXAMPLES["update"]
        name = self.body_name()
        self.expect("on")
        self.expect("the")
        self.expect("map")
        mp = self.name()
        solids = []
        if self.accept("with"):
            self.expect("solid")
            solids.append(self.arith())
            while self.accept("and") or (self.peek() is not None and self.peek().kind == "OP" and self.peek().value == "," and not self.advance()):
                solids.append(self.arith())
        self.end()
        return ("update", line, name, mp, solids)

    def advance(self):
        self.i += 1
        return False

    def st_bodymove(self):
        line = self.lineno
        self.example = EXAMPLES["move"]
        name = self.body_name()
        self.expect("to")
        x = self.arith()
        self.comma("the spot")
        y = self.arith()
        self.end()
        return ("bodymove", line, name, x, y)

    def physics_factor(self):
        """the x of the body NAME | the y of ... | the horizontal speed of ... | the vertical speed of ... |
        the body NAME is on the ground / is falling / is facing left"""
        w = self.peek().value
        if w == "the" and self.peek(1) is not None:
            a = self.peek(1).value
            if a in ("x", "y") and self.word("of", 2) and self.word("the", 3) and self.word("body", 4):
                self.i += 5
                return ("bodyval", a, self.name())
            if a in ("horizontal", "vertical") and self.word("speed", 2) and self.word("of", 3) and self.word("the", 4) and self.word("body", 5):
                self.i += 6
                return ("bodyval", "vx" if a == "horizontal" else "vy", self.name())
            if a == "body" and "body" not in self.declared:
                save = self.i
                self.i += 2
                name = self.name()
                if self.words("is", "on", "the", "ground"):
                    self.i += 4
                    return ("bodyval", "ground", name)
                if self.words("is", "falling"):
                    self.i += 2
                    return ("bodyval", "falling", name)
                if self.words("is", "facing", "left"):
                    self.i += 3
                    return ("bodyval", "left", name)
                self.i = save
        return None


class PhysicsRun:
    def physics_init(self):
        self.bodies = {}

    def body_named(self, name):
        b = self.bodies.get(name)
        if b is None:
            from .errors import suggest
            hint = suggest(name, list(self.bodies))
            raise self.err(f'I don\'t know a body called "{name}".', (hint + "  " if hint else "") + "Make it first: make a body called " + name + " at 20, 20 with size 12 by 16")
        return b

    def x_body(self, s, env):
        _, line, name, o = s
        w = self.dnumber(o["size"][0], env, "The body's width")
        h = self.dnumber(o["size"][1], env, "The body's height")
        if w <= 0 or h <= 0:
            raise self.err("A body's size must be more than 0.")
        x = self.dnumber(o["at"][0], env, "The body's first spot number") if "at" in o else 0
        y = self.dnumber(o["at"][1], env, "The body's second spot number") if "at" in o else 0
        b = {"x": x, "y": y, "vx": 0, "vy": 0, "w": w, "h": h, "ground": False, "left": False, "run": 0, "solid": ("#",)}
        for k, d in DEFAULTS.items():
            b[k] = self.dnumber(o[k], env, f'The body\'s {k}') if k in o else d
        self.bodies[name] = b

    def x_bodydo(self, s, env):
        _, line, name, action = s
        b = self.body_named(name)
        if action == "run left":
            b["run"], b["left"] = -1, True
        elif action == "run right":
            b["run"], b["left"] = 1, False
        elif action == "stop":
            b["run"] = 0
        elif action == "jump":
            if b["ground"]:
                b["vy"], b["ground"] = -b["jump"], False
        else:
            b["vy"], b["ground"] = -b["jump"], False

    def x_bodymove(self, s, env):
        _, line, name, x, y = s
        b = self.body_named(name)
        b["x"], b["y"] = self.dnumber(x, env, "The first spot number"), self.dnumber(y, env, "The second spot number")
        b["vx"] = b["vy"] = b["run"] = 0
        b["ground"] = False

    def x_update(self, s, env):
        _, line, name, mp, solids = s
        b = self.body_named(name)
        m = self.map_named(mp)
        chars = tuple(self.fmt(self.ev(e, env)) for e in solids) if solids else ("#",)
        t, rows = m["tile"], m["rows"]
        height, width = len(rows), len(rows[0])

        def solid(px, py):
            c, r = math.floor(px / t), math.floor(py / t)
            if c < 0:
                return True  # the left edge of the world is a wall
            if 0 <= r < height and c < width:
                return rows[r][c] in chars
            return False

        w, h = b["w"], b["h"]
        # across: move, and stop at a wall
        b["vx"] = b["run"] * b["speed"]
        nx = b["x"] + b["vx"]
        edge = nx + w - 0.01 if b["vx"] > 0 else nx
        if b["vx"] != 0 and (solid(edge, b["y"] + 0.5) or solid(edge, b["y"] + h - 0.5) or solid(edge, b["y"] + h / 2)):
            nx = (math.floor(edge / t) * t - w) if b["vx"] > 0 else (math.floor(edge / t) + 1) * t
            b["vx"] = 0
        b["x"] = nx
        # down and up: gravity, landing, bumping heads
        b["vy"] = min(b["vy"] + b["gravity"], MAX_FALL)
        ny = b["y"] + b["vy"]
        b["ground"] = False
        if b["vy"] > 0:
            if solid(b["x"] + 0.5, ny + h) or solid(b["x"] + w - 0.5, ny + h):
                ny = math.floor((ny + h) / t) * t - h
                b["vy"], b["ground"] = 0, True
        elif b["vy"] < 0:
            if solid(b["x"] + 0.5, ny) or solid(b["x"] + w - 0.5, ny):
                ny = (math.floor(ny / t) + 1) * t
                b["vy"] = 0
        b["y"] = ny

    def e_bodyval(self, n, env):
        _, what, name = n
        b = self.body_named(name)
        if what == "falling":
            return b["vy"] > 0 and not b["ground"]
        v = b[what]
        if isinstance(v, bool):
            return v
        v = round(v, 3)
        return int(v) if v == int(v) else v
