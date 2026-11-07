"""Running a game. The program makes sprites and maps and describes a game (`play a game ...`);
then a host (the browser engine, `hl play`, or a test) calls game_frame() again and again.
Each call runs the game's handlers once and gives back what to draw: a list of plain commands.
"""
import math

from .errors import suggest
from .game import SOUNDS
from .designrun import DRAWABLE
from .render import size_px

MAX_SPRITES = 200
MAX_MAP_CELLS = 250000
MAX_COMMANDS = 20000
FRAME_SECONDS = 2  # one frame may think for this long before HL stops the game


class GameRun:
    """Mixed into the Interpreter."""

    def game_init(self):
        self.sprites, self.maps, self.game = {}, {}, None
        self.frame_cmds = None
        self.sounds, self.changed_maps = [], set()
        self.cam = (0, 0)
        self.keys_down = set()
        self.mouse = (0, 0)

    # -- declaring ---------------------------------------------------------------------
    def x_sprite(self, s, env):
        _, line, name, ps, frames, extra = s
        if len(self.sprites) >= MAX_SPRITES and name not in self.sprites:
            raise self.err(f"A game can have at most {MAX_SPRITES} sprites.")
        rows = extra["rows"]
        per = len(rows) // frames
        self.sprites[name] = {"rows": rows, "legend": extra["legend"], "ps": ps, "frames": frames,
                              "w": len(rows[0]) * ps, "h": per * ps}

    def x_map(self, s, env):
        _, line, name, tile, extra = s
        rows = extra["rows"]
        if len(rows) * len(rows[0]) > MAX_MAP_CELLS:
            raise self.err(f"A map can have at most {MAX_MAP_CELLS} tiles.")
        for letter, what in extra["legend"].items():
            if isinstance(what, list) and what[1] not in self.sprites:
                hint = suggest(what[1], list(self.sprites))
                raise self.err(f'The map "{name}" uses the sprite "{what[1]}", but there is no such sprite (yet).',
                               (hint + "  " if hint else "") + f'Make it first, above the map: make a sprite called {what[1]}')
        self.maps[name] = {"rows": [list(r) for r in rows], "legend": extra["legend"], "tile": tile}
        self.changed_maps.add(name)

    def x_game(self, s, env):
        _, line, title, width, height, bg, handlers = s
        if self.game is not None:
            raise self.err("A program can have only one game.", "Put everything in one: play a game ...")
        w = self.dnumber(width, env, "The game's width")
        h = self.dnumber(height, env, "The game's height")
        if not (40 <= w <= 4000 and 40 <= h <= 4000):
            raise self.err(f"A game's size is 40 to 4000 in each direction, but this one is {w} by {h}.")
        colour = "#000000"
        if bg is not None:
            colour = self.dprops([("background", bg)], env)["background"]
            if colour == "none":
                colour = "#000000"
        self.game = {"title": self.limited(self.fmt(self.ev(title, env))), "w": w, "h": h, "bg": colour,
                     "env": env, "handlers": [], "started": False, "over": False, "frame": 0, "time": 0.0}
        for kind, arg, body, hline in handlers:
            h_ = {"kind": kind, "arg": arg, "body": body, "line": hline, "next": 0.0}
            if kind == "every":
                secs = self.dnumber(arg, env, "The time between runs")
                if secs <= 0:
                    raise self.err(f'"every ... seconds" needs more than 0 seconds, but got {secs}.')
                h_["arg"] = secs
                h_["next"] = secs
            self.game["handlers"].append(h_)

    # -- statements used while a frame is drawn -------------------------------------------------
    def needs_frame(self, what):
        if self.frame_cmds is None:
            raise self.err(f'"{what}" only works while a game is running.',
                           'Use it inside the game: "every frame", "when the game starts", a key part... or in a function those call.')

    def push(self, cmd):
        if len(self.frame_cmds) >= MAX_COMMANDS:
            raise self.err(f"One frame of the game has more than {MAX_COMMANDS} things to draw, so I stopped it.")
        self.frame_cmds.append(cmd)

    def sprite_named(self, name):
        sp = self.sprites.get(name)
        if sp is None:
            hint = suggest(name, list(self.sprites))
            raise self.err(f'I don\'t know a sprite called "{name}".',
                           (hint + "  " if hint else "") + 'Make it first: make a sprite called ' + name)
        return sp

    def map_named(self, name):
        m = self.maps.get(name)
        if m is None:
            hint = suggest(name, list(self.maps))
            raise self.err(f'I don\'t know a map called "{name}".', (hint + "  " if hint else "") + "Make it first: make a map called " + name)
        return m

    def x_drawsprite(self, s, env):
        _, line, name, x, y, opts = s
        self.needs_frame("draw")
        sp = self.sprite_named(name)
        px = self.dnumber(x, env, "The sprite's first number (across)")
        py = self.dnumber(y, env, "The sprite's second number (down)")
        frame = 0
        if "frame" in opts:
            frame = self.dnumber(opts["frame"], env, "The sprite's frame")
            if frame != int(frame) or not (1 <= frame <= sp["frames"]):
                raise self.err(f'The sprite "{name}" has {sp["frames"]} frame{"s" if sp["frames"] != 1 else ""}, '
                               f"so a frame is a whole number from 1 to {sp['frames']}, but this is {frame}.")
            frame = int(frame) - 1
        flip = bool(self.ev(opts["flip"], env)) if "flip" in opts else False
        self.push(["sprite", name, px - self.cam[0], py - self.cam[1], frame, flip])

    def x_drawmap(self, s, env):
        self.needs_frame("draw")
        name = s[2]
        self.map_named(name)
        self.push(["map", name, -self.cam[0], -self.cam[1]])

    def x_camera(self, s, env):
        _, line, x, y = s
        self.cam = (self.dnumber(x, env, "The camera's first number (across)"), self.dnumber(y, env, "The camera's second number (down)"))

    def x_sound(self, s, env):
        name = self.fmt(self.ev(s[2], env)).lower()
        if name not in SOUNDS:
            hint = suggest(name, list(SOUNDS))
            raise self.err(f'I don\'t have a sound called "{name}".', (hint + "  " if hint else "") + "Sounds: " + ", ".join(SOUNDS) + ".")
        if self.frame_cmds is not None and len(self.sounds) < 30:
            self.sounds.append(name)

    def x_stopgame(self, s, env):
        if self.game is None:
            raise self.err('"stop the game" only works while a game is running.')
        self.game["over"] = True

    def tile_cell(self, m, mode, a, b):
        if mode == "pixel":
            return math.floor(a / m["tile"]), math.floor(b / m["tile"])
        return int(a) - 1, int(b) - 1  # people count columns and rows from 1

    def x_settile(self, s, env):
        _, line, mode, a, b, name, value = s
        m = self.map_named(name)
        c, r = self.tile_cell(m, mode, self.dnumber(a, env, "The first number"), self.dnumber(b, env, "The second number"))
        v = self.ev(value, env)
        v = " " if v is None else self.fmt(v)
        if len(v) != 1:
            raise self.err(f'A tile is one letter, but this is {len(v)} letters: "{v}".', 'Example: change the tile at x, y of maze to "."')
        if v not in m["legend"]:
            raise self.err(f'The map "{name}" has nothing for the letter "{v}".', f'Add a line like: where "{v}" is red   (or use ".")')
        if 0 <= r < len(m["rows"]) and 0 <= c < len(m["rows"][0]) and m["rows"][r][c] != v:
            m["rows"][r][c] = v
            self.changed_maps.add(name)

    def game_put(self, s, env):
        """`put a circle at ...` while a game runs: a shape drawn this frame."""
        _, line, kind, content, name, pos, points, props, body, extra = s
        if kind not in DRAWABLE:
            raise self.err(f"A game can draw shapes, pixel art and text, but not a {kind}.")
        node = {"kind": kind}
        if content is not None:
            node["text"] = self.limited(self.fmt(self.ev(content, env)))
        cx, cy = (0, 0) if kind == "text" else self.cam  # words stay on the screen (like a score); shapes move with the camera
        if pos is not None:
            node["at"] = (self.dnumber(pos[0], env, "The spot's first number (across)") - cx,
                          self.dnumber(pos[1], env, "The spot's second number (down)") - cy)
        elif kind == "text":
            raise self.err("In a game, a text needs a spot: put a text \"Score\" at 10, 10")
        if points:
            node["points"] = [(self.dnumber(x, env, "A corner's first number") - cx, self.dnumber(y, env, "A corner's second number") - cy)
                              for x, y in points]
        node["props"] = self.dprops(props, env)
        if kind == "text":
            node["props"]["px"] = size_px(node["props"].get("size", "normal"))
        if extra is not None:
            node["rows"], node["legend"] = extra["rows"], extra["legend"]
        self.push(["shape", node])

    # -- expressions -------------------------------------------------------------------------------
    def e_keydown(self, n, env):
        return n[1] in self.keys_down

    def e_mousepos(self, n, env):
        return self.mouse[0 if n[1] == "x" else 1]

    def e_framenumber(self, n, env):
        return self.game["frame"] if self.game else 0

    def e_gametime(self, n, env):
        return round(self.game["time"], 2) if self.game else 0

    def e_tileat(self, n, env):
        _, mode, a, b, name = n
        m = self.map_named(name)
        c, r = self.tile_cell(m, mode, self.dnumber(a, env, "The first number"), self.dnumber(b, env, "The second number"))
        if 0 <= r < len(m["rows"]) and 0 <= c < len(m["rows"][0]):
            ch = m["rows"][r][c]
            return "." if ch == "." else ch
        return ""

    def e_gridsize(self, n, env):
        m = self.map_named(n[2])
        return len(m["rows"][0]) if n[1] == "columns" else len(m["rows"])

    def e_touch(self, n, env):
        _, a, ax, ay, b, bx, by = n
        sa, sb = self.sprite_named(a), self.sprite_named(b)
        ax, ay = self.dnumber(ax, env, "The first spot's number"), self.dnumber(ay, env, "The first spot's number")
        bx, by = self.dnumber(bx, env, "The second spot's number"), self.dnumber(by, env, "The second spot's number")
        return ax < bx + sb["w"] and bx < ax + sa["w"] and ay < by + sb["h"] and by < ay + sa["h"]

    # -- the host's side -----------------------------------------------------------------------------
    def game_info(self):
        """Everything the screen needs once, before the first frame."""
        g = self.game
        if g is None:
            return None
        self.changed_maps = set()
        return {"title": g["title"], "w": g["w"], "h": g["h"], "bg": g["bg"],
                "sprites": {k: {"rows": v["rows"], "legend": v["legend"], "ps": v["ps"], "frames": v["frames"]}
                            for k, v in self.sprites.items()},
                "maps": self.maps_snapshot(self.maps), "sounds": list(SOUNDS)}

    def maps_snapshot(self, names):
        return {k: {"rows": ["".join(r) for r in self.maps[k]["rows"]], "legend": self.maps[k]["legend"],
                    "tile": self.maps[k]["tile"]} for k in names}

    def run_handler(self, h):
        from .interpreter import Env, StopSignal
        local = Env(self.game["env"])
        self.line = h["line"]
        try:
            self.exec_block(h["body"], local)
        except StopSignal:
            pass

    def game_frame(self, down=(), pressed=(), clicked=False, mouse=None, dt=1 / 60):
        """Run one frame. down: keys held now; pressed: keys that went down since the last frame.
        Returns {"cmds": [...], "sounds": [...], "maps": {...changed maps...}, "over": bool}."""
        g = self.game
        if g is None:
            raise self.err("This program doesn't have a game: there is no \"play a game\" in it.")
        self.keys_down = set(down)
        if mouse is not None:
            self.mouse = (mouse[0], mouse[1])
        self.frame_cmds, self.sounds = [], []
        if not g["over"]:
            self.set_time_limit(FRAME_SECONDS)
            try:
                handlers = g["handlers"]
                if not g["started"]:
                    g["started"] = True
                    for h in handlers:
                        if h["kind"] == "start":
                            self.run_handler(h)
                g["time"] += dt
                for h in handlers:
                    if g["over"]:
                        break
                    if h["kind"] == "key" and h["arg"] in pressed:
                        self.run_handler(h)
                    elif h["kind"] == "click" and clicked:
                        self.run_handler(h)
                for h in handlers:
                    if h["kind"] == "every":
                        runs = 0
                        while g["time"] >= h["next"] and runs < 5 and not g["over"]:
                            h["next"] += h["arg"]
                            runs += 1
                            self.run_handler(h)
                        if g["time"] >= h["next"]:  # fell far behind: don't try to catch up
                            h["next"] = g["time"] + h["arg"]
                for h in handlers:
                    if h["kind"] == "frame" and not g["over"]:
                        self.run_handler(h)
                g["frame"] += 1
            finally:
                self.set_time_limit(0)
        changed = self.maps_snapshot(self.changed_maps)
        self.changed_maps = set()
        out = {"cmds": self.frame_cmds, "sounds": self.sounds, "maps": changed, "over": g["over"]}
        self.frame_cmds = None
        return out
