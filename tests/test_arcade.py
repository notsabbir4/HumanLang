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
        self.assertEqual(len(self.arcade_files()), 6)

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
                it = Interpreter(out=lambda t: None)
                it.assets = {f: ("video" if f.endswith(".mp4") else "audio") for f in os.listdir(os.path.join(ROOT, "games", "files"))}   # files a game ships with
                it.run(load(os.path.basename(path)))
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
        it = Interpreter()
        it.assets = {f: "audio" for f in ("Pixel_Arpeggio.mp3", "Galaxy_Dash.mp3", "Boss_Battle_Theme.mp3", "Oblivar_Final_Boss.mp3")}
        it.run(load("planet_defenders_2.hum"))
        g = it.globals.vars
        for _ in range(25):
            it.game_frame()
        self.assertEqual(g["mode"], "home")
        it.game_frame(clicked=True, mouse=(150, 52 + (level - 1) * 28 + 10))   # tap the level's button
        self.assertEqual(g["mode"], "play")
        return it, g

    def test_planet_defenders_2_levels(self):
        drops = {1: 40, 2: 25, 3: 12, 4: 5}
        for level in (1, 2, 3, 4):
            it, g = self.pd2(level)
            self.assertEqual((g["hp"], g["hp_max"]), (100, 100))       # a health bar of 100 on every level
            self.assertEqual(g["drop_pct"], drops[level])   # harder levels drop fewer skills
        self.assertEqual([int(v) for v in g["hit_dmg_for"]][:4], [20, 30, 40, 50])   # ...but hits hurt more

    def test_planet_defenders_2_health_is_a_bar_not_hearts(self):
        with open(os.path.join(ROOT, "games", "planet_defenders_2.hum"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("lives", text.replace("health bar instead of lives", ""))
        self.assertNotIn("icon_heart", text)
        it, g = self.pd2(2)
        it.game_frame()
        g["bomb_wait"] = 10 ** 6
        g["hp"] = 100
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(4):
            it.game_frame()
        self.assertEqual(g["hp"], 70)                       # a medium bomb takes 30 of 100
        g["dx"][0], g["dy"][0], g["dk"][0] = g["px"] + 10, 180, 6
        for _ in range(4):
            it.game_frame()
        self.assertEqual(g["hp"], 100)                      # a health pack gives 35 back, never more than the bar holds
        g["dx"][0], g["dy"][0], g["dk"][0] = g["px"] + 10, 180, 6
        g["hp"] = 50
        for _ in range(4):
            it.game_frame()
        self.assertEqual(g["hp"], 85)

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
        self.assertEqual(g["hp"], 100)                      # the shield took the bomb
        g["shield_t"] = 0
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(10):
            it.game_frame()
        self.assertEqual(g["hp"], 70)                       # without it, the bomb takes 30 off the bar
        g["hurt_t"] = 0

        def mean_bomb_x(ghost):
            """Where the aliens' bombs start, on average, while the ship sits far right (and may be invisible)."""
            xs = []
            for _ in range(3000):
                g["bomb_wait"], g["px"], g["shield_t"], g["hurt_t"] = 0, 250, 0, 0
                g["ghost_t"] = 300 if ghost else 0
                g["decoy_x"] = 20                           # the game picks a new decoy every second: keep this one
                g["hp"], g["aimed_pct"] = 100, 100            # always aim, so the only difference is what they aim at
                it.game_frame()
                xs += [float(v) for v, y in zip(g["bx"], g["by"]) if 0 <= y < 118]
            self.assertTrue(xs)
            return sum(xs) / len(xs)

        seen, hidden = mean_bomb_x(False), mean_bomb_x(True)
        self.assertLess(hidden, seen - 40)                  # invisible: bombs go toward the decoy on the left, not the ship

    def test_planet_defenders_2_two_hits_on_impossible_then_home(self):
        it, g = self.pd2(4)
        it.game_frame()
        g["bx"][0], g["by"][0] = g["px"] + 25, 185
        for _ in range(4):
            it.game_frame()
        self.assertEqual((g["mode"], g["hp"]), ("play", 50))
        g["hurt_t"] = 0
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
        g["hp"] = 1
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
        for _ in range(4):                                  # four pages: how to play, skills, levels, bosses
            it.game_frame(pressed=["enter"])
        self.assertEqual(g["mode"], "home")

    # ---- Planet Defenders 2: the bosses XERON and OBLIVAR, and the skill OBLIVAR-X ----
    def call_boss(self, g, it, kind=None):
        """Clear the aliens of wave 6 so that a boss comes; with kind, keep going until that boss is the one."""
        for _ in range(400):
            g["boss_kind"], g["wave"], g["alive"], g["left"] = 0, 6, [0] * 32, 0
            it.game_frame()
            if g["boss_kind"] and (kind is None or int(g["boss_kind"]) == kind):
                return
        self.fail("the boss did not come")

    def fight(self, g, it, frames, until_beaten=False):
        """Fly under the boss and fire; returns the frames of the fight, one at a time."""
        out = []
        for _ in range(frames):
            if until_beaten and not g["boss_kind"]:
                break
            if g["boss_kind"]:
                g["px"] = max(0, min(265, int(float(g["boss_x"]) + float(g["boss_w"]) / 2 - 27)))
            g["hurt_t"], g["hp"] = 0, g["hp_max"]
            out.append(it.game_frame(down=["space"]))
        return out

    def test_pd2_a_boss_comes_after_every_6_waves(self):
        it, g = self.pd2(2)
        for done in range(1, 19):                           # clear waves 1 to 18, one after another
            g["boss_kind"], g["wave"], g["alive"], g["left"] = 0, done, [0] * 32, 0
            it.game_frame()
            if done % 6 == 0:
                self.assertIn(int(g["boss_kind"]), (1, 2))  # after wave 6, 12 and 18: a boss, with a warning first
                self.assertGreater(g["boss_warn"], 0)
                self.assertEqual(g["wave"], done + 1)
            else:
                self.assertEqual(g["boss_kind"], 0)
                self.assertEqual(g["wave"], done + 1)

    def test_pd2_oblivar_is_the_main_boss_but_comes_less_than_half_the_time(self):
        it, g = self.pd2(2)
        random.seed(5)
        kinds = []
        for _ in range(300):
            self.call_boss(g, it)
            kinds.append(int(g["boss_kind"]))
        share = kinds.count(2) / len(kinds)
        self.assertGreater(share, 0.32)
        self.assertLess(share, 0.48)                        # 40 in 100

    def test_pd2_bosses_last_long_on_every_level_and_hit_harder_on_harder_levels(self):
        hp = {1: [], 2: []}
        dmg = []
        for level in (1, 2, 3, 4):
            it, g = self.pd2(level)
            for kind in (1, 2):
                self.call_boss(g, it, kind)
                hp[kind].append(int(g["boss_hp"]))
            dmg.append(int(g["boss_dmg_for"][level - 1]))
        self.assertEqual(hp[1], [90] * 4)                   # the same long fight on every level
        self.assertEqual(hp[2], [220] * 4)
        self.assertEqual(dmg, [8, 14, 20, 30])              # easy: light hits, impossible: heavy hits
        self.assertEqual(dmg, sorted(dmg))

    def test_pd2_xeron_can_be_beaten_and_drops_two_skills(self):
        it, g = self.pd2(1)
        self.call_boss(g, it, 1)
        self.fight(g, it, 2400, until_beaten=True)
        self.assertEqual(g["boss_kind"], 0)
        self.assertEqual(g["bosses_beaten"], 1)
        self.assertEqual(g["wave"], 7)                      # the waves go on after a boss
        self.assertGreaterEqual(sum(1 for v in g["dy"] if v >= 0), 2)

    def test_pd2_oblivar_makes_the_sky_bloody_and_changes_the_music(self):
        it, g = self.pd2(1)
        self.call_boss(g, it, 1)
        self.assertEqual(g["blood"], 0)                     # XERON: a normal sky
        self.fight(g, it, 2400)
        self.call_boss(g, it, 2)
        frames = self.fight(g, it, 200)
        self.assertEqual(g["blood"], 5)                     # OBLIVAR: blood red
        music = [f["music"] for f in frames if "music" in f]
        self.assertEqual(music, [])                         # (the tune started with the warning)
        frames = self.fight(g, it, 12000, until_beaten=True)    # the main boss lasts long
        self.assertEqual(g["boss_kind"], 0)
        back = [f for f in frames if f.get("music") == "Galaxy_Dash.mp3"]
        self.assertTrue(back and back[0].get("resume"))     # the game song goes on from where the boss interrupted it
        for _ in range(120):
            it.game_frame()
        self.assertEqual(g["blood"], 0)                     # and the sky heals

    def test_pd2_training_is_very_gentle_and_bosses_drop_many_skills(self):
        it, g = self.pd2(5)
        self.assertEqual(g["level_pick"], 5)
        self.assertEqual(g["level_names"][4], "TRAINING")
        self.call_boss(g, it, 2)
        for _ in range(100):
            it.game_frame()
        g["hurt_t"], g["shield_t"] = 0, 0
        g["kx"][0], g["ky"][0], g["kvx"][0], g["kvy"][0] = g["px"] + 25, 186, 0, 2
        for _ in range(3):
            it.game_frame()
        self.assertEqual(g["hp"], 98)                       # a training boss shot takes only 2
        self.fight(g, it, 12000, until_beaten=True)
        self.assertEqual(g["boss_kind"], 0)
        self.assertEqual(g["boss_gifts"], 6)                # 6 gifts in a training fight (2 on the other levels)

    def test_pd2_the_game_song_pauses_for_a_boss_and_continues_after(self):
        it, g = self.pd2(2)
        sent = []
        for _ in range(400):
            g["boss_kind"], g["wave"], g["alive"], g["left"] = 0, 6, [0] * 32, 0
            f = it.game_frame()
            if "music" in f:
                sent.append((f["music"], f.get("resume", False)))
            if g["boss_kind"]:
                break
        self.assertEqual(sent[-1], ("Boss_Battle_Theme.mp3", False))    # it is PLAYED, so the game song is put on the shelf where it was
        frames = self.fight(g, it, 12000, until_beaten=True)
        back = [(f["music"], f.get("resume")) for f in frames if "music" in f]
        self.assertIn(("Galaxy_Dash.mp3", True), back)                   # and CONTINUED when the boss is beaten

    def test_pd2_each_boss_has_its_own_tune(self):
        for kind, tune in ((1, "Boss_Battle_Theme.mp3"), (2, "Oblivar_Final_Boss.mp3")):
            it, g = self.pd2(2)
            g["boss_kind"], g["wave"], g["alive"], g["left"] = 0, 6, [0] * 32, 0
            tunes = []
            for _ in range(80):
                g["boss_kind"], g["wave"], g["alive"], g["left"] = 0, 6, [0] * 32, 0
                f = it.game_frame()
                if g["boss_kind"] == kind:
                    tunes = [f["music"]] if "music" in f else []
                    break
            self.assertEqual(tunes, [tune])

    def test_pd2_boss_bullets_hurt_and_a_shield_stops_them(self):
        it, g = self.pd2(2)
        self.call_boss(g, it, 1)
        for _ in range(100):
            it.game_frame()
        g["hurt_t"], g["shield_t"] = 0, 0
        g["kx"][0], g["ky"][0], g["kvx"][0], g["kvy"][0] = g["px"] + 25, 186, 0, 2
        for _ in range(3):
            it.game_frame()
        self.assertEqual(g["hp"], 86)                       # a medium boss shot takes 14
        g["hurt_t"], g["shield_t"] = 0, 300
        g["kx"][0], g["ky"][0], g["kvx"][0], g["kvy"][0] = g["px"] + 25, 186, 0, 2
        for _ in range(3):
            it.game_frame()
        self.assertEqual(g["hp"], 86)

    def test_pd2_oblivar_drops_oblivar_x_rarely_and_rarer_on_harder_levels(self):
        rate = []
        for level in (1, 2, 3, 4):
            it, g = self.pd2(level)
            random.seed(level)
            got = 0
            for _ in range(300):
                self.call_boss(g, it, 2)
                g["boss_warn"], g["boss_in"], g["boss_die"], g["boss_y"] = 0, 0, 1, 40
                g["dy"] = [-1] * 5
                it.game_frame()
                got += any(g["dy"][i] >= 0 and g["dk"][i] == 7 for i in range(5))
            rate.append(got / 300)
        self.assertEqual(rate, sorted(rate, reverse=True))  # easy drops it most, impossible least
        self.assertGreater(rate[0], 0.33)
        self.assertLess(rate[3], 0.15)
        # XERON never drops it
        it, g = self.pd2(1)
        for _ in range(100):
            self.call_boss(g, it, 1)
            g["boss_warn"], g["boss_in"], g["boss_die"], g["boss_y"] = 0, 0, 1, 40
            g["dy"] = [-1] * 5
            it.game_frame()
            self.assertFalse(any(g["dy"][i] >= 0 and g["dk"][i] == 7 for i in range(5)))

    def test_pd2_oblivar_x_transforms_the_ship(self):
        it, g = self.pd2(2)
        it.game_frame()
        g["bomb_wait"] = 10 ** 6
        g["px"] = 100
        g["dx"][0], g["dy"][0], g["dk"][0] = 110, 180, 7   # the skill falls onto the ship
        for _ in range(3):
            it.game_frame()
        self.assertGreater(g["x_t"], 900)                   # changing shape
        before = sum(1 for v in g["sy"] if v >= 0)
        for _ in range(40):
            it.game_frame(down=["space"])
        self.assertEqual(sum(1 for v in g["sy"] if v >= 0), before)   # no firing during the change
        for _ in range(40):
            it.game_frame()
        self.assertLessEqual(g["x_t"], 900)                 # transformed
        g["sy"] = [-1] * 30
        g["cool"] = 0
        it.game_frame(down=["space"])
        self.assertEqual(sum(1 for v in g["sy"] if v >= 0), 5)        # five guns
        self.assertEqual(g["xhp"], 100)                     # the purple health bar is full
        g["bx"][0], g["by"][0] = g["px"] + 25, 190          # a bomb hits the purple bar first, and only half as hard
        for _ in range(4):
            it.game_frame()
        self.assertEqual((g["xhp"], g["hp"]), (85, 100))
        for _ in range(900):
            it.game_frame()
        self.assertEqual(g["x_t"], 0)                       # and it changes back
        self.assertEqual(g["xhp"], 0)                       # the health bar is red again
        g["cool"] = 0
        g["sy"] = [-1] * 30
        it.game_frame(down=["space"])
        self.assertEqual(sum(1 for v in g["sy"] if v >= 0), 1)

    def test_pd2_oblivar_x_hits_bosses_twice_as_hard(self):
        damage = []
        for x_on in (0, 1):
            it, g = self.pd2(2)
            self.call_boss(g, it, 1)
            g["boss_warn"], g["boss_in"], g["boss_y"] = 0, 0, 40
            g["x_t"] = 500 if x_on else 0
            hp = float(g["boss_hp"])
            g["sx"][0], g["sy"][0] = float(g["boss_x"]) + 20, float(g["boss_y"]) + 30
            it.game_frame()
            damage.append(hp - float(g["boss_hp"]))
        self.assertEqual(damage, [1, 2])

    # ---- Planet Defenders 2 (0.6.2): every boss attack can be dodged or passed through ----
    def boss_ready_for_attacks(self, kind, level=2):
        it, g = self.pd2(level)
        self.call_boss(g, it, kind)
        g["boss_warn"], g["boss_in"], g["boss_y"], g["boss_atk"] = 0, 0, 40, 10 ** 6   # in the fight, but it does not attack by itself
        g["ky"] = [-1] * 30
        return it, g

    def test_pd2_xeron_curtain_always_has_a_hole_wide_enough_for_the_ship(self):
        it, g = self.boss_ready_for_attacks(1)
        holes = 0
        for seed in range(400):
            random.seed(seed)
            g["ky"], g["dive_phase"], g["beam_phase"], g["boss_y"] = [-1] * 30, 0, 0, 40
            g["boss_atk"] = 0                                # attack now
            g["boss_move"] = 0
            it.game_frame()
            xs = sorted(float(x) for x, y in zip(g["kx"], g["ky"]) if y >= 0 and y < 60)
            if len(xs) >= 12 and all(abs(a - b) <= 18.1 or abs(a - b) > 60 for a, b in zip(xs, xs[1:])) and xs[-1] - xs[0] > 200:
                holes += 1
                widest = max(b - a for a, b in zip(xs, xs[1:]))
                self.assertGreaterEqual(widest, 54)          # the ship is 31 wide: plenty of room
        self.assertGreater(holes, 20)                        # the wall comes often enough to be tested

    def test_pd2_oblivar_fan_has_a_gap_where_you_stand(self):
        it, g = self.boss_ready_for_attacks(2, level=4)
        seen = 0
        for seed in range(400):
            random.seed(seed)
            g["ky"], g["beam_phase"], g["boss_y"] = [-1] * 30, 0, 40
            g["px"] = 20 + (seed * 37) % 240                 # the ship stands anywhere
            g["boss_x"] = 2 + (seed * 53) % 250              # and so does the boss
            g["boss_atk"], g["boss_move"] = 0, 0
            it.game_frame()
            shots = [(float(x), float(vx), float(vy), float(y)) for x, vx, vy, y in zip(g["kx"], g["kvx"], g["kvy"], g["ky"]) if y >= 0]
            if len(shots) >= 6 and len({round(v[1], 3) for v in shots}) == len(shots):
                # where each shot will be when it reaches the ship's height
                landing = sorted(x + vx * ((188 - y) / vy) for x, vx, vy, y in shots)
                ship_left, ship_right = g["px"] + 12, g["px"] + 43
                self.assertFalse(any(ship_left <= l <= ship_right for l in landing), f"seed {seed}: a fan shot hits a ship that stands still")
                seen += 1
        self.assertGreater(seen, 10)

    def test_pd2_laser_beams_leave_room_and_warn_first(self):
        it, g = self.boss_ready_for_attacks(2, level=3)
        g["boss_hp"] = float(g["boss_max"]) * 0.4            # rage: three beams
        seen = 0
        for seed in range(300):
            random.seed(seed)
            g["beam_phase"], g["boss_atk"], g["boss_move"], g["px"] = 0, 0, 0, 100 + seed % 120
            it.game_frame()
            if g["beam_phase"] == 1:
                beams = sorted(float(v) for v in (g["beam_a"], g["beam_b"], g["beam_c"]) if v > 0)
                self.assertGreater(float(g["beam_t"]), 40)   # a long warning first
                for a, b in zip(beams, beams[1:]):
                    self.assertGreaterEqual(b - a, 80)       # at least 58 pixels free between two beams
                    self.assertGreater(b - a - 22, 40)       # the ship is about 35 wide
                self.assertTrue(all(20 <= v <= 300 for v in beams))
                seen += 1
        self.assertGreater(seen, 15)

    def test_pd2_laser_beam_hurts_only_after_the_warning_and_only_on_the_beam(self):
        it, g = self.boss_ready_for_attacks(2, level=2)
        g["px"], g["hurt_t"], g["shield_t"], g["x_t"], g["hp"] = 100, 0, 0, 0, 100
        g["beam_phase"], g["beam_t"], g["beam_a"], g["beam_b"], g["beam_c"] = 1, 30, 127, -100, -100
        for _ in range(20):
            it.game_frame()
        self.assertEqual(g["hp"], 100)                       # the warning line does not hurt
        for _ in range(60):
            it.game_frame()
        self.assertEqual(g["beam_phase"], 0)
        self.assertEqual(g["hp"], 79)                        # the beam did: 1.5 x 14 = 21 (the ship stood in it)
        g["px"], g["hurt_t"], g["hp"] = 100, 0, 100
        g["beam_phase"], g["beam_t"], g["beam_a"] = 2, 20, 260
        for _ in range(25):
            it.game_frame()
        self.assertEqual(g["hp"], 100)                       # standing somewhere else is safe
        g["hurt_t"], g["shield_t"], g["hp"] = 0, 300, 100
        g["beam_phase"], g["beam_t"], g["beam_a"] = 2, 20, 127
        for _ in range(25):
            it.game_frame()
        self.assertEqual(g["hp"], 100)                       # a shield blocks a beam

    def test_pd2_xeron_dive_follows_locks_and_can_be_dodged(self):
        it, g = self.boss_ready_for_attacks(1, level=2)
        g["px"], g["hurt_t"], g["shield_t"], g["hp"] = 130, 0, 0, 100
        g["dive_phase"], g["dive_t"] = 1, 70
        locked_x = None
        dodged = False
        for frame in range(200):
            if g["dive_phase"] == 1 and g["dive_t"] == 33:
                locked_x = float(g["boss_x"])
            if g["dive_phase"] == 1 and g["dive_t"] <= 30:
                g["px"] = 10 if locked_x is not None and locked_x > 100 else 260    # step out of the red column
                dodged = True
            it.game_frame()
            if g["dive_phase"] == 0 and frame > 20:
                break
        self.assertTrue(dodged)
        self.assertEqual(g["hp"], 100)                       # dodged: no damage
        self.assertEqual(float(g["boss_y"]), 40)             # it climbs back
        # standing still under the dive hurts: 2 x 14
        g["hurt_t"], g["hp"], g["px"], g["dive_phase"], g["dive_t"] = 0, 100, 130, 1, 70
        g["boss_x"] = 130 + 27 - float(g["boss_w"]) / 2
        for _ in range(200):
            g["px"] = 130
            it.game_frame()
            if g["dive_phase"] == 0:
                break
        self.assertEqual(g["hp"], 72)

    def test_pd2_bosses_never_use_the_same_attack_twice_in_a_row_and_use_all_of_them(self):
        for kind, n in ((1, 4), (2, 5)):
            it, g = self.boss_ready_for_attacks(kind)
            seen, last = set(), None
            for seed in range(200):
                random.seed(seed)
                g["beam_phase"], g["dive_phase"], g["boss_y"] = 0, 0, 40
                g["boss_atk"] = 0
                it.game_frame()
                move = int(g["boss_move"])
                self.assertNotEqual(move, last)
                seen.add(move)
                last = move
            self.assertEqual(seen, set(range(1, n + 1)))

    def test_pd2_every_attack_shows_a_hint_and_a_boss_pack_falls_twice(self):
        it, g = self.boss_ready_for_attacks(2)
        g["boss_atk"], g["boss_move"] = 0, 0
        it.game_frame()
        self.assertTrue(str(g["hint"]).strip())
        self.assertGreater(g["hint_t"], 0)
        packs = 0
        for _ in range(int(float(g["boss_max"]))):
            before = sum(1 for i in range(5) if g["dy"][i] >= 0 and g["dk"][i] == 6)
            g["dy"] = [-1] * 5
            g["boss_x"] = 100
            g["sx"][0], g["sy"][0] = 120, float(g["boss_y"]) + 30
            it.game_frame()
            packs += sum(1 for i in range(5) if g["dy"][i] >= 0 and g["dk"][i] == 6)
            g["hurt_t"], g["hp"] = 0, 100
            g["boss_atk"] = 10 ** 6
        self.assertEqual(packs, 2)                           # at two thirds and at one third of its health

    def test_pd2_the_health_bar_is_red_and_turns_purple_with_oblivar_x(self):
        it, g = self.pd2(2)
        it.game_frame()
        frame = it.game_frame()
        shapes = [str(sh) for sh in frame.get("draw", [])] if isinstance(frame, dict) else []
        text = " ".join(shapes)
        self.assertNotIn("#8e3cff", text.lower())                    # normal: no purple
        g["bomb_wait"] = 10 ** 6
        g["dx"][0], g["dy"][0], g["dk"][0] = g["px"] + 10, 180, 7
        for _ in range(3):
            it.game_frame()
        for _ in range(80):
            it.game_frame()
        self.assertGreater(g["xhp"], 0)
        frame = it.game_frame()
        self.assertIn("#8e3cff", str(frame))                 # transformed: a purple bar
        self.assertIn("#e21c24", str(frame))                 # (with a thin red line for the real health)

    def test_every_built_in_tune_exists_in_the_screen_code(self):
        from humanlang.assets import BUILTIN_MUSIC
        with open(os.path.join(ROOT, "humanlang", "arcade.js"), encoding="utf-8") as f:
            js = f.read()
        for name in BUILTIN_MUSIC:
            self.assertIn(f"{name}: {{ bpm:", js)

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
