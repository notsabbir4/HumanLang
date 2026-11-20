"""HumanLang Odyssey: the video plays first, the code gates really work, and World 1 and World 5 can be finished."""
import json
import os
import sys
import unittest

from humanlang.interpreter import Interpreter

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools", "odyssey"))
import levels  # noqa: E402

with open(os.path.join(ROOT, "games", "humanlang_odyssey.hum"), encoding="utf-8") as f:
    CODE = f.read()


class Game:
    def __init__(self):
        self.it = Interpreter()
        self.it.assets = {"humanlang_intro.mp4": "video"}
        self.it.run(CODE)

    def var(self, n):
        e = self.it.game["env"].find(n)
        return e.vars[n] if e else None

    def fr(self, down=(), pressed=()):
        return self.it.game_frame(down=down, pressed=pressed)

    @property
    def hero(self):
        return self.it.bodies["hero"]

    def to_world(self, door_index):
        self.fr(); self.fr(); self.fr(pressed=["enter"])
        target = levels.HUB_DOORS[door_index] + 4
        for _ in range(3000):
            if self.hero["x"] >= target:
                break
            self.fr(down=["right"])
        self.fr(pressed=["enter"])


class Odyssey(unittest.TestCase):
    def test_listed_with_version_and_video_file(self):
        with open(os.path.join(ROOT, "games", "index.json"), encoding="utf-8") as f:
            g = [x for x in json.load(f) if x["id"] == "humanlang-odyssey"][0]
        self.assertEqual(g["version"], "0.6.2")
        self.assertIn("humanlang_intro.mp4", g["files"])
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "games", "files", "humanlang_intro.mp4")))

    def test_video_plays_on_the_first_frame_then_the_title(self):
        g = Game()
        self.assertEqual(g.fr().get("video"), "humanlang_intro.mp4")
        self.assertEqual(g.var("mode"), "title")
        self.assertIsNone(g.fr().get("video"))

    def test_screen_and_art_sizes(self):
        info = Game().it.game_info()
        self.assertEqual((info["w"], info["h"]), (480, 270))
        self.assertIn("make a sprite called hero with pixel size 1", CODE)

    def test_gates_are_wall_until_solved_and_world_1_finishes(self):
        g = Game()
        g.to_world(0)
        self.assertEqual(g.var("mode"), "w1")
        for _ in range(4000):                    # without the puzzle the hero cannot pass gate 1
            if g.var("talk_on") in (True, "yes"):
                g.fr(pressed=["enter"])
            else:
                g.fr(down=["right"])
            if g.hero["x"] > levels.W1_GATE1_X:
                break
        self.assertLess(g.hero["x"], levels.W1_GATE1_X)
        for n in range(8000):
            if g.var("mode") != "w1":
                break
            down, pressed = ["right"], []
            if g.var("talk_on") in (True, "yes"):
                down = []
                pressed = ["enter"] if n % 5 == 0 else []
            elif g.var("pz"):
                down = []
                if n % 6 == 0:
                    pressed = ["enter"]
                    if g.var("pz_stage") == "pick":
                        if g.var("pz_sel") < g.var("pz_answer")[g.var("pz") - 1]:
                            pressed = ["right"]
            else:
                if n % 50 == 0:
                    down.append("space")
                if n % 9 == 0:
                    pressed = ["enter"]
            g.fr(down=down, pressed=pressed)
        self.assertEqual(g.var("mode"), "w1done")
        self.assertEqual(g.var("w1_done"), 1)

    def test_a_wrong_answer_does_not_open_the_gate(self):
        g = Game()
        g.to_world(0)
        for _ in range(1500):
            if g.var("talk_on") in (True, "yes"):
                g.fr(pressed=["enter"])
            else:
                g.fr(down=["right"])
        g.fr(pressed=["enter"])
        self.assertEqual(g.var("pz"), 1)
        g.fr(pressed=["enter"])              # picks option 1, which is wrong
        g.fr(pressed=["enter"])              # shows the result, then goes back to choosing
        self.assertFalse(g.var("gate1_open") in (True, "yes"))
        self.assertEqual(g.var("pz_stage"), "pick")

    def test_world_5_can_be_finished_by_a_simple_bot(self):
        g = Game()
        g.to_world(4)
        self.assertEqual(g.var("mode"), "w5")
        rows = levels.world5().text()

        def ground_row(c):
            for r in range(17):
                if 0 <= c < 130 and rows[r][c] in "NS":
                    return r
            return 99
        for _ in range(12000):
            if g.var("mode") != "w5":
                break
            b, on = g.hero, g.hero["ground"]
            c, feet = int((b["x"] + 11) / 16), int((b["y"] + 40) / 16)
            here, nxt = ground_row(c), ground_row(c + 1)
            down = ["right"]
            if on and nxt != here and float(b["x"]) + 22 > (c + 1) * 16 - 6:
                down.append("space")
            for bx, by in zip(g.var("bug_x"), g.var("bug_y")):
                if on and 0 < float(bx) - float(b["x"]) < 60 and abs(float(by) - float(b["y"])) < 30:
                    down.append("space")
            g.fr(down=down)
        self.assertEqual(g.var("mode"), "w5done")
        self.assertEqual(g.var("w5_done"), 1)


if __name__ == "__main__":
    unittest.main()
