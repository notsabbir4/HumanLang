"""Games: sprites, tile maps, keys and a frame loop, in plain words.

    make a sprite called ship
        where "g" is green
        "..g.."
        "ggggg"

    set x to 100
    play a game titled "Blaster" with size 320 by 240 and background black
        when the game starts
            set score to 0
        every frame
            if key "left" is down
                change x to x - 3
            draw the sprite ship at x, 200

This file READS that (a Parser mixin). gamerun.py runs it; the browser engine (website/static/arcade.js) draws it.
"""
from .errors import suggest

KEY_NAMES = (["left", "right", "up", "down", "space", "enter", "escape", "shift", "tab", "backspace"]
             + [chr(c) for c in range(ord("a"), ord("z") + 1)] + [str(d) for d in range(10)])
SOUNDS = ("jump", "coin", "hit", "shoot", "explosion", "powerup", "win", "lose", "beep", "blip", "step")

EXAMPLES = {
    "sprite": 'make a sprite called ship\n    where "g" is green\n    "..g.."\n    "ggggg"',
    "map": 'make a map called level with tile size 16\n    where "#" is blue\n    "#####"\n    "#...#"\n    "#####"',
    "game": 'play a game titled "My game" with size 320 by 240 and background black',
    "draw": "draw the sprite ship at 100, 200",
    "handler": "when the game starts   /   every frame   /   every 2 seconds   /   when the key \"space\" is pressed",
}


class GameParser:
    in_game = 0

    # -- helpers ----------------------------------------------------------------------
    def number_literal(self, what):
        t = self.peek()
        if t is None or t.kind != "NUM":
            self.fail(f"I expected a number for {what}")
        self.i += 1
        return t.value

    def joiner(self):
        """Skip the little words and commas between options: 'with', 'and', ','."""
        moved = False
        while True:
            t = self.peek()
            if t is not None and t.kind == "OP" and t.value == ",":
                self.i += 1
            elif self.accept("and") or self.accept("with"):
                pass
            else:
                return moved
            moved = True

    # -- make a sprite / make a map ---------------------------------------------------
    def st_make(self):
        line, lvl = self.lineno, self.level
        self.expect("a")
        t = self.peek()
        kind = t.value if t is not None and t.kind == "WORD" else None
        if kind not in ("sprite", "map", "body"):
            self.example = EXAMPLES["sprite"]
            self.fail('After "make a" I expected "sprite", "map" or "body"')
        self.i += 1
        if kind == "body":
            return self.make_body(line)
        self.example = EXAMPLES[kind]
        self.expect("called")
        name = self.name()
        ps, frames, tile = 4, 1, 16
        self.joiner()
        while self.peek() is not None:
            if self.words("pixel", "size") and kind == "sprite":
                self.i += 2
                ps = self.number_literal("the pixel size")
            elif self.words("tile", "size") and kind == "map":
                self.i += 2
                tile = self.number_literal("the tile size")
            elif kind == "sprite" and self.peek().kind == "NUM" and (self.word("frames", 1) or self.word("frame", 1)):
                frames = self.number_literal("the number of frames")
                self.i += 1
            else:
                break
            self.joiner()
        self.end()
        if kind == "sprite":
            if not (0 < ps <= 64) or not (0 < frames <= 64) or frames != int(frames):
                self.fail("A sprite's pixel size is 1 to 64, and its frames are a whole number from 1 to 64")
        elif not (2 <= tile <= 256):
            self.fail("A map's tile size is 2 to 256")
        extra = self.pixel_rows(lvl, allow_sprites=(kind == "map"))
        if kind == "sprite":
            if len(extra["rows"]) % int(frames):
                self.fail(f"This sprite has {int(frames)} frames, so its number of rows ({len(extra['rows'])}) must divide evenly: "
                          f"every frame has the same number of rows")
            return ("sprite", line, name, ps, int(frames), extra)
        return ("map", line, name, tile, extra)

    # -- play a game -------------------------------------------------------------------
    def st_play(self):
        line, lvl = self.lineno, self.level
        if self.words("the", "music"):
            self.i += 2
            self.example = 'play the music "adventure"'
            music = self.arith()
            self.end()
            return ("music", line, music)
        if self.words("the", "sound"):
            self.i += 2
            self.example = 'play the sound "coin"'
            sound = self.arith()
            self.end()
            return ("sound", line, sound)
        self.example = EXAMPLES["game"]
        self.expect("a")
        self.expect("game")
        if self.in_game:
            self.fail("A game can't be inside another game")
        title = ("lit", "HumanLang game")
        if self.accept("titled") or self.accept("called"):
            self.design_content = True
            try:
                title = self.arith()
            finally:
                self.design_content = False
        width, height, bg = ("lit", 320), ("lit", 240), None
        self.joiner()
        while self.peek() is not None:
            if self.word("size"):
                self.i += 1
                width = self.arith()
                self.expect("by")
                height = self.arith()
            elif self.word("background"):
                self.i += 1
                bg = self.colour_words("background")
            else:
                break
            self.joiner()
        self.end()
        handlers = []
        self.in_game += 1
        try:
            if not (self.pos < len(self.lines) and self.lines[self.pos].indent > lvl):
                self.fail("A game needs its parts, indented below it",
                          hint='Example:\nplay a game titled "Demo"\n    every frame\n        draw the sprite ship at 10, 10')
            while self.pos < len(self.lines) and self.lines[self.pos].indent > lvl:
                ln = self.lines[self.pos]
                if ln.indent != lvl + 1:
                    self.lineno = ln.no
                    self.fail("This line is indented too far", hint="Indent by exactly 4 spaces under the game line.")
                self.pos += 1
                self.load(ln)
                self.example = EXAMPLES["handler"]
                handlers.append(self.handler_header(ln.indent))
        finally:
            self.in_game -= 1
        return ("game", line, title, width, height, bg, handlers)

    def handler_header(self, lvl):
        line = self.lineno
        if self.words("when", "the", "game", "starts") or self.words("when", "the", "game", "starts"):
            self.i += 4
            kind, arg = "start", None
        elif self.words("every", "frame"):
            self.i += 2
            kind, arg = "frame", None
        elif self.word("every"):
            self.i += 1
            arg = self.arith()
            if not (self.accept("seconds") or self.accept("second")):
                self.fail('After "every ... " I expected "seconds", like: every 2 seconds')
            kind = "every"
        elif self.words("when", "the", "key"):
            self.i += 3
            t = self.peek()
            if t is None or t.kind != "STR" or any(p[0] != "t" for p in t.value):
                self.fail('After "the key" I expected the key in quotes, like: when the key "space" is pressed')
            self.i += 1
            arg = self.key_name("".join(p[1] for p in t.value))
            self.expect("is")
            self.expect("pressed")
            kind = "key"
        elif self.words("when", "the", "mouse", "is", "clicked"):
            self.i += 5
            kind, arg = "click", None
        else:
            t = self.peek()
            self.fail(f'I didn\'t expect "{self.show(t)}" here: inside a game, each part starts with one of these',
                      hint="when the game starts\nevery frame\nevery 2 seconds\n"
                           'when the key "space" is pressed\nwhen the mouse is clicked')
        self.end()
        body = self.body(lvl)
        return (kind, arg, body, line)

    def key_name(self, name):
        name = name.lower()
        if name not in KEY_NAMES:
            hint = suggest(name, KEY_NAMES)
            self.fail(f'I don\'t know a key called "{name}"',
                      hint=(hint + "  " if hint else "") + "Keys: left, right, up, down, space, enter, escape, shift, a to z, 0 to 9.")
        return name

    # -- drawing, camera, tiles -----------------------------------------------------------
    def st_draw(self):
        line = self.lineno
        self.example = EXAMPLES["draw"]
        if not (self.in_game or self.in_function):
            self.fail('"draw" only works inside a game (in "every frame" or in a function a game uses)')
        self.expect("the")
        if self.accept("picture"):
            self.example = 'draw the picture "face.png" at 10, 20 with size 32 by 32'
            name = self.arith()
            self.expect("at")
            x = self.arith()
            self.comma("the spot")
            y = self.arith()
            size = None
            if self.accept("with"):
                self.expect("size")
                w = self.arith()
                self.expect("by")
                size = (w, self.arith())
            self.end()
            return ("drawpicture", line, name, x, y, size)
        if self.accept("map"):
            name = self.name()
            self.end()
            return ("drawmap", line, name)
        self.expect("sprite")
        name = self.name()
        self.expect("at")
        opts = {}
        if self.words("the", "body"):
            body = self.body_name()
            x, y = ("bodyval", "x", body), ("bodyval", "y", body)
            opts["flip"] = ("bodyval", "left", body)
        else:
            x = self.arith()
            self.comma("the spot")
            y = self.arith()
        self.joiner()
        while self.peek() is not None:
            if self.words("facing", "left") or self.words("facing", "right"):
                left = self.peek(1).value == "left"
                self.i += 2
                if left and self.accept("when"):  # facing left when going_left
                    opts["flip"] = self.arith()
                else:
                    opts["flip"] = ("lit", left)
            elif self.accept("flipped"):
                opts["flip"] = self.arith() if self.accept("when") else ("lit", True)
            elif self.word("frame"):
                self.i += 1
                opts["frame"] = self.arith()
            else:
                break
            self.joiner()
        self.end()
        return ("drawsprite", line, name, x, y, opts)

    def st_move(self):
        line = self.lineno
        self.example = "move the camera to 100, 0"
        self.expect("the")
        self.expect("camera")
        self.expect("to")
        x = self.arith()
        self.comma("the camera spot")
        y = self.arith()
        self.end()
        return ("camera", line, x, y)

    def st_changetile(self):
        """change the tile in column 3, row 2 of maze to "x"   |   change the tile at x, y of maze to "x" """
        line = self.lineno
        self.example = 'change the tile in column 3, row 2 of maze to "."'
        self.accept("the")
        self.expect("tile")
        if self.accept("in"):
            self.expect("column")
            a = self.arith()
            self.comma("the tile")
            self.expect("row")
            mode = "cell"
        else:
            self.expect("at")
            a = self.arith()
            self.comma("the spot")
            mode = "pixel"
        b = self.arith()
        self.expect("of")
        name = self.name()
        self.expect("to")
        value = self.arith()
        self.end()
        return ("settile", line, mode, a, b, name, value)

    # -- expressions (called from Parser.factor) ----------------------------------------------
    def game_factor(self):
        """Words that only mean something in a game. Returns a node, or None if this isn't one."""
        t = self.peek()
        w = t.value
        if w == "key" and "key" not in self.declared and self.peek(1) is not None and self.peek(1).kind == "STR":
            s = self.peek(1)
            if any(p[0] != "t" for p in s.value):
                self.fail('A key name is plain text in quotes, like key "left" is down')
            name = self.key_name("".join(p[1] for p in s.value))
            self.i += 2
            self.expect("is")
            self.expect("down")
            return ("keydown", name)
        if w == "mouse" and "mouse" not in self.declared and self.peek(1) is not None and self.peek(1).value in ("x", "y") \
                and self.peek(1).kind == "WORD":
            self.i += 2
            return ("mousepos", self.toks[self.i - 1].value)
        if w == "tile" and "tile" not in self.declared:
            if self.word("at", 1):
                self.i += 2
                a = self.arith()
                self.comma("the spot")
                b = self.arith()
                self.expect("of")
                return ("tileat", "pixel", a, b, self.name())
            if self.word("in", 1) and self.word("column", 2):
                self.i += 3
                a = self.arith()
                self.comma("the tile")
                self.expect("row")
                b = self.arith()
                self.expect("of")
                return ("tileat", "cell", a, b, self.name())
        if self.words("how", "many", "columns", "in") or self.words("how", "many", "rows", "in"):
            which = self.peek(2).value
            self.i += 4
            return ("gridsize", which, self.name())
        if self.words("the", "frame", "number") or self.words("frame", "number"):
            self.i += 3 if w == "the" else 2
            return ("framenumber",)
        if self.words("game", "time") or self.words("the", "game", "time"):
            self.i += 3 if w == "the" else 2
            return ("gametime",)
        if w == "the" and self.word("sprite", 1) and "sprite" not in self.declared:
            self.i += 2
            a = self.name()
            self.expect("at")
            ax = self.arith()
            self.comma("the first spot")
            ay = self.arith()
            self.expect("touches")
            self.expect("the")
            self.expect("sprite")
            b = self.name()
            self.expect("at")
            bx = self.arith()
            self.comma("the second spot")
            by = self.arith()
            return ("touch", a, ax, ay, b, bx, by)
        return None
