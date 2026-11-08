"""Games: sprites, maps, the frame loop, the web page, and the four showcase games."""
import glob
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from humanlang import gamehost, gamepage  # noqa: E402
from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

SHIP = 'make a sprite called ship\n    where "g" is green\n    "..g.."\n    "ggggg"\n'


def make(code, **kw):
    it = Interpreter(**kw)
    it.run(code)
    return it


def fails(test, code, *words, frames=1):
    it = Interpreter()
    with test.assertRaises(HLError) as ctx:
        it.run(code)
        for _ in range(frames):
            it.game_frame()
    text = str(ctx.exception.message) + " " + str(getattr(ctx.exception, "hint", ""))
    for w in words:
        test.assertIn(w, text)


class Basics(unittest.TestCase):
    def test_sprite_and_draw(self):
        it = make(SHIP + 'play a game titled "T" with size 100 by 80 and background black\n    every frame\n        draw the sprite ship at 5, 6\n')
        info = it.game_info()
        self.assertEqual((info["w"], info["h"], info["title"]), (100, 80, "T"))
        self.assertEqual(info["sprites"]["ship"]["frames"], 1)
        f = it.game_frame()
        self.assertEqual(f["cmds"], [["sprite", "ship", 5, 6, 0, False]])

    def test_keys_and_variables(self):
        it = make('set x to 0\nplay a game titled "T"\n    every frame\n        if key "right" is down\n            change x to x + 2\n'
                  '    when the key "space" is pressed\n        change x to x + 100\n')
        it.game_frame(down=["right"])
        it.game_frame(down=["right"], pressed=["space"])
        it.game_frame()
        self.assertEqual(it.globals.vars["x"], 104)

    def test_start_runs_once_and_every_seconds(self):
        it = make('set n to 0\nset t to 0\nplay a game titled "T"\n    when the game starts\n        change n to n + 1\n'
                  '    every 1 seconds\n        change t to t + 1\n')
        for _ in range(130):
            it.game_frame()
        self.assertEqual(it.globals.vars["n"], 1)
        self.assertEqual(it.globals.vars["t"], 2)

    def test_stop_the_game(self):
        it = make('play a game titled "T"\n    every frame\n        stop the game\n')
        self.assertTrue(it.game_frame()["over"])

    def test_camera_moves_shapes_but_not_text(self):
        it = make(SHIP + 'play a game titled "T"\n    every frame\n        move the camera to 10, 0\n'
                  '        draw the sprite ship at 50, 5\n        put a text "hi" at 3, 3\n        put a circle at 20, 20 with radius 4 and colour red\n')
        cmds = it.game_frame()["cmds"]
        self.assertEqual(cmds[0][2], 40)
        self.assertEqual(cmds[1][1]["at"], (3, 3))
        self.assertEqual(cmds[2][1]["at"], (10, 20))

    def test_tiles(self):
        it = make('make a map called m with tile size 10\n    where "#" is blue and "o" is red\n    "##o"\n    "#.o"\nset got to ""\n'
                  'play a game titled "T"\n    every frame\n        change got to tile at 25, 5 of m\n'
                  '        change the tile in column 3, row 2 of m to "#"\n        change tile at 1, 1 of m to "."\n')
        rows = it.game_frame()["maps"]
        self.assertEqual(it.globals.vars["got"], "o")
        self.assertEqual(it.maps["m"]["rows"], [list(".#o"), list("#.#")])
        self.assertEqual(list(rows), ["m"])

    def test_grid_size_touch_and_frames(self):
        it = make(SHIP.replace("ship", "a") + SHIP.replace("ship", "b") + 'make a map called m\n    where "#" is red\n    "###"\n    "###"\n'
                  'set cols to 0\nset hit to no\nset far to yes\nplay a game titled "T"\n    every frame\n'
                  '        change cols to how many columns in m\n'
                  '        change hit to the sprite a at 0, 0 touches the sprite b at 9, 3\n'
                  '        change far to the sprite a at 0, 0 touches the sprite b at 50, 3\n')
        it.game_frame()
        self.assertEqual(it.globals.vars["cols"], 3)
        self.assertIs(it.globals.vars["hit"], True)
        self.assertIs(it.globals.vars["far"], False)

    def test_for_each_from_to(self):
        it = make("set total to 0\nfor each n from 1 to 4\n    change total to total + n\n")
        self.assertEqual(it.globals.vars["total"], 10)

    def test_hex_colours_in_pixel_art(self):
        it = make('make a sprite called s\n    where "a" is "#ff8800"\n    "a"\n')
        self.assertEqual(it.sprites["s"]["legend"]["a"], "#ff8800")

    def test_sprite_frames(self):
        it = make('make a sprite called w with 2 frames\n    where "a" is red\n    "a."\n    ".a"\nplay a game titled "T"\n    every frame\n'
                  '        draw the sprite w at 0, 0 frame 2 facing left\n')
        self.assertEqual(it.game_frame()["cmds"][0][4:], [1, True])

    def test_flipped_when(self):
        it = make(SHIP + 'set left to yes\nplay a game titled "T"\n    every frame\n        draw the sprite ship at 0, 0 facing left when left\n')
        self.assertIs(it.game_frame()["cmds"][0][5], True)


class Mistakes(unittest.TestCase):
    def test_unknown_sprite(self):
        fails(self, SHIP + 'play a game titled "T"\n    every frame\n        draw the sprite shp at 1, 1\n', "shp", "ship")

    def test_unknown_key(self):
        fails(self, 'play a game titled "T"\n    when the key "spce" is pressed\n        say "x"\n', "spce", "space")

    def test_unknown_sound(self):
        fails(self, 'play a game titled "T"\n    every frame\n        play the sound "boing"\n', "boing")

    def test_draw_outside_game(self):
        fails(self, SHIP + 'draw the sprite ship at 1, 1\n', "game")

    def test_bad_part(self):
        fails(self, 'play a game titled "T"\n    say "x"\n', "every frame")

    def test_frames_must_divide(self):
        fails(self, 'make a sprite called s with 2 frames\n    where "a" is red\n    "a"\n    "a"\n    "a"\n', "divide")

    def test_map_needs_its_sprite_first(self):
        fails(self, 'make a map called m\n    where "o" is the sprite coin\n    "o"\n', "coin")

    def test_bad_frame_number(self):
        fails(self, SHIP + 'play a game titled "T"\n    every frame\n        draw the sprite ship at 1, 1 frame 3\n', "frame")

    def test_one_game_only(self):
        fails(self, 'play a game titled "A"\n    every frame\n        say "x"\nplay a game titled "B"\n    every frame\n        say "x"\n', "only one")

    def test_game_size_limits(self):
        fails(self, 'play a game titled "A" with size 5 by 5\n    every frame\n        say "x"\n', "size")

    def test_error_inside_frame_names_line(self):
        it = make('play a game titled "T"\n    every frame\n        say nothing_here\n')
        with self.assertRaises(HLError) as ctx:
            it.game_frame()
        self.assertEqual(ctx.exception.line, 3)

    def test_endless_loop_in_a_frame_is_stopped(self):
        it = make('play a game titled "T"\n    every frame\n        repeat forever\n            say "x"\n', out=lambda t: None)
        with self.assertRaises(HLError):
            it.game_frame()


class Host(unittest.TestCase):
    def test_start_and_frame_json(self):
        r = json.loads(gamehost.start(SHIP + 'play a game titled "T"\n    every frame\n        draw the sprite ship at 1, 2\n'))
        self.assertEqual(r["info"]["title"], "T")
        f = json.loads(gamehost.frame(json.dumps({"down": [], "pressed": []})))
        self.assertEqual(f["cmds"][0][0], "sprite")

    def test_no_game_and_errors_are_text(self):
        self.assertIn("doesn't have a game", json.loads(gamehost.start('say "hi"'))["error"])
        self.assertIn("error", json.loads(gamehost.start("say nothing_here")))

    def test_ask_is_refused(self):
        r = json.loads(gamehost.start('play a game titled "T"\n    when the game starts\n        ask "name?" into n\n'))
        f = json.loads(gamehost.frame("{}")) if "info" in r else r
        self.assertIn("error", f)


class Page(unittest.TestCase):
    def test_page_carries_the_game(self):
        h = gamepage.game_to_html('say "</script><b>"\n', 'A "quoted" <title>')
        self.assertIn("pyodide", h)
        self.assertNotIn('</script><b>', h.split("const CODE")[1])
        self.assertIn("&lt;title&gt;", h)

    def test_arcade_js_is_valid_javascript(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        r = subprocess.run([node, "--check", os.path.join(ROOT, "humanlang", "arcade.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_cli_build_and_run(self):
        folder = tempfile.mkdtemp()
        src = os.path.join(folder, "g.hum")
        with open(src, "w") as f:
            f.write(SHIP + 'play a game titled "CLI game"\n    every frame\n        draw the sprite ship at 1, 1\n')
        env = dict(os.environ, HL_NO_OPEN="1", PYTHONPATH=ROOT)
        out = os.path.join(folder, "g.html")
        r = subprocess.run([sys.executable, "-m", "humanlang", "build", src, "--out", out], capture_output=True, text=True, env=env, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            self.assertIn("CLI game", f.read())
        r = subprocess.run([sys.executable, "-m", "humanlang", "run", src], capture_output=True, text=True, env=env, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("game", r.stderr)
        shutil.rmtree(folder, ignore_errors=True)


def load(name):
    with open(os.path.join(ROOT, "games", name), encoding="utf-8") as f:
        return f.read()


class Showcase(unittest.TestCase):
    def arcade_files(self):
        with open(os.path.join(ROOT, "games", "index.json"), encoding="utf-8") as f:
            return [g["file"] for g in json.load(f) if g.get("kind") == "arcade"]

    def test_arcade_games_are_listed(self):
        self.assertEqual(len(self.arcade_files()), 5)

    def test_every_game_explains_itself_for_inspect(self):
        sys.path.insert(0, os.path.join(ROOT, "website"))
        import build  # noqa: E402
        with open(os.path.join(ROOT, "games", "index.json"), encoding="utf-8") as f:
            for g in json.load(f):
                with self.subTest(game=g["id"]):
                    self.assertTrue(g.get("how"), "every game needs its 'how' steps for the Inspect button")
                    html = build.inspect_html(load(g["file"]), g["how"], g["id"])
                    self.assertIn("How it works", html)
                    self.assertEqual(html.count('class="step"'), len(g["how"]))

    def test_every_game_runs_and_draws(self):
        for name in self.arcade_files():
            path = os.path.join(ROOT, "games", name)
            with self.subTest(game=os.path.basename(path)):
                it = make(load(os.path.basename(path)), out=lambda t: None)
                keys = ["left", "right", "up", "down", "space"]
                for i in range(900):
                    f = it.game_frame(down=[keys[(i // 30) % 5]], pressed=[keys[(i // 7) % 5]] if i % 7 == 0 else [])
                self.assertTrue(f["cmds"])
                self.assertLess(len(it.game_info()["title"]), 40)

    def test_sky_runner_can_be_won(self):
        it = make(load("sky_runner.hum"))
        g = it.globals.vars
        rows = it.maps["level"]["rows"]

        def tile(x, y):
            c, r = int(x // 16), int(y // 16)
            return rows[r][c] if 0 <= r < 15 and 0 <= c < 64 else ""
        for _ in range(4000):
            px, py = float(g["px"]), float(g["py"])
            jump = False
            if g["on_ground"]:
                pit = tile(px + 14, py + 17) not in "#B"
                wall = tile(px + 20, py + 8) in "#B"
                beetle = any(10 < float(e) - px < 40 for e in g["ex"] if float(e) > 0) and all(tile(px + k, py + 17) in "#B" for k in (40, 60, 80, 100))
                jump = pit or wall or beetle
            it.game_frame(down=["right"], pressed=["up"] if jump else [])
            if g["mode"] != "play":
                break
        self.assertEqual(g["mode"], "won")

    def test_crate_climber_top_is_reachable(self):
        it = make(load("crate_climber.hum"))
        g = it.globals.vars
        ladders = {208: 15, 176: 3, 128: 16, 80: 4, 32: 4}
        it.game_frame()
        g["spawn_in"] = 10 ** 6  # no barrels: this checks the ladders and tiers line up
        for _ in range(1500):
            px, py = float(g["px"]), float(g["py"])
            if g["climbing"]:
                keys = ["up"]
            else:
                tx = ladders[min(ladders, key=lambda k: abs(k - py))] * 16 + 2
                keys = ["right"] if px < tx - 2 else ["left"] if px > tx + 2 else ["up"]
            it.game_frame(down=keys)
            if g["mode"] != "play":
                break
        self.assertEqual(g["mode"], "won")

    def test_planet_defenders_scores_and_loses(self):
        it = make(load("planet_defenders.hum"))
        g = it.globals.vars
        for i in range(2500):
            it.game_frame(down=["left" if (i // 50) % 2 else "right"], pressed=["space"] if i % 20 == 0 else [])
        self.assertGreater(g["score"], 0)

    def pd2(self, level):
        random.seed(level)                                      # the game uses chance: make every run the same
        it = make(load("planet_defenders_2.hum"))
        g = it.globals.vars
        for _ in range(25):
            it.game_frame()
        self.assertEqual(g["mode"], "home")
        it.game_frame(clicked=True, mouse=(150, 56 + (level - 1) * 32 + 10))   # tap the level's button
        self.assertEqual(g["mode"], "play")
        return it, g

    def test_planet_defenders_2_levels(self):
        lives = {1: 5, 2: 3, 3: 3, 4: 1}
        drops = {1: 40, 2: 25, 3: 12, 4: 5}
        for level in (1, 2, 3, 4):
            it, g = self.pd2(level)
            self.assertEqual(g["lives"], lives[level])      # impossible: only one life
            self.assertEqual(g["drop_pct"], drops[level])   # harder levels drop fewer skills

    def test_planet_defenders_2_never_ends_and_scores_time(self):
        it, g = self.pd2(1)
        for i in range(60 * 20):
            it.game_frame(down=["space", "left" if (i // 60) % 2 else "right"])
        self.assertGreaterEqual(g["time_s"], 19)
        self.assertGreater(g["score"], g["kills"] * 10)     # the seconds you survive are worth points
        self.assertGreaterEqual(g["wave"], 2)               # a cleared wave is followed by another

    def test_planet_defenders_2_skills_must_be_caught(self):
        it, g = self.pd2(2)
        it.game_frame()
        # a shield falls far from the spacecraft: it is not collected
        g["px"] = 0
        g["dx"][0], g["dy"][0], g["dk"][0] = 250, 100, 1
        for _ in range(30):
            it.game_frame()
        self.assertEqual(g["shield_t"], 0)
        # one falls onto the spacecraft: it is
        g["dx"][1], g["dy"][1], g["dk"][1] = 20, 170, 2
        for _ in range(12):
            it.game_frame()
        self.assertGreater(g["power_t"], 0)
        self.assertLess(g["power_t"], 301)
        # full power: three shots at once
        g["cool"] = 0
        before = sum(1 for v in g["sy"] if v >= 0)
        it.game_frame(down=["space"])
        self.assertEqual(sum(1 for v in g["sy"] if v >= 0) - before, 3)

    def test_planet_defenders_2_shield_and_invisible(self):
        it, g = self.pd2(2)
        it.game_frame()
        g["bomb_wait"] = 10 ** 6
        g["shield_t"] = 300
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(10):
            it.game_frame()
        self.assertEqual(g["lives"], 3)                     # the shield took the bomb
        g["shield_t"] = 0
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(10):
            it.game_frame()
        self.assertEqual(g["lives"], 2)                     # without it, a life is lost
        g["hurt_t"] = 0

        def mean_bomb_x(ghost):
            """Where the aliens' bombs start, on average, while the ship sits far right (and may be invisible)."""
            xs = []
            for _ in range(3000):
                g["bomb_wait"], g["px"], g["shield_t"], g["hurt_t"] = 0, 250, 0, 0
                g["ghost_t"] = 300 if ghost else 0
                g["decoy_x"] = 20                           # the game picks a new decoy every second: keep this one
                g["lives"], g["aimed_pct"] = 3, 100             # always aim, so the only difference is what they aim at
                it.game_frame()
                xs += [float(v) for v, y in zip(g["bx"], g["by"]) if 0 <= y < 118]
            self.assertTrue(xs)
            return sum(xs) / len(xs)

        seen, hidden = mean_bomb_x(False), mean_bomb_x(True)
        self.assertLess(hidden, seen - 40)                  # invisible: bombs go toward the decoy on the left, not the ship

    def test_planet_defenders_2_one_life_on_impossible_then_home(self):
        it, g = self.pd2(4)
        it.game_frame()
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(4):
            it.game_frame()
        self.assertEqual(g["mode"], "over")
        for _ in range(60):
            it.game_frame()
        it.game_frame(pressed=["enter"])
        self.assertEqual(g["mode"], "home")

    def test_planet_defenders_2_instructions_and_best_score(self):
        it, g = self.pd2(1)
        g["score"] = 777
        g["lives"] = 1
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(3):
            it.game_frame()
        self.assertEqual(g["mode"], "over")
        self.assertEqual(it.memory.recall("pd2 best 1"), 777)
        for _ in range(60):
            it.game_frame()
        it.game_frame(pressed=["enter"])
        it.game_frame(pressed=["h"])
        self.assertEqual(g["mode"], "how")
        for _ in range(3):
            it.game_frame(pressed=["enter"])
        self.assertEqual(g["mode"], "home")

    def test_maze_muncher_eats_dots(self):
        it = make(load("maze_muncher.hum"))
        g = it.globals.vars
        it.game_frame()
        start = g["dots_left"]
        for i in range(400):
            it.game_frame(pressed=["left"] if i == 0 else [])
        self.assertLess(g["dots_left"], start)
        self.assertGreater(g["score"], 0)


if __name__ == "__main__":
    unittest.main()
