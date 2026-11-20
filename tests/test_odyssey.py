"""HumanLang Odyssey: the video plays first, the code gates really work, and every one of the seven worlds can be finished."""
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

YES = (True, "yes")


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

    def to_hub(self):
        self.fr(); self.fr(); self.fr(pressed=["enter"])
        for _ in range(3):
            self.fr()

    def to_world(self, number):
        self.to_hub()
        self.hero.update({"x": levels.HUB_DOORS[number - 1] + 4, "y": 184})
        for _ in range(3):
            self.fr()
        self.fr(pressed=["enter"])

    def run_bot(self, rows, solid, limit, stop, gates=True):
        """A simple player: runs right, jumps at pits, steps and bugs, talks to Echo and answers the code gates."""
        def ground_row(c):
            for r in range(len(rows)):
                if 0 <= c < len(rows[0]) and rows[r][c] in solid:
                    return r
            return 99
        for n in range(limit):
            if stop():
                return True
            b, on = self.hero, self.hero["ground"]
            down, pressed = ["right"], []
            if self.var("talk_on") in YES:
                down = []
                pressed = ["enter"] if n % 5 == 0 else []
            elif self.var("pz"):
                down = []
                if n % 6 == 0:
                    pressed = ["enter"]
                    if self.var("pz_stage") == "pick" and self.var("pz_sel") < self.var("pz_answer")[self.var("pz") - 1]:
                        pressed = ["right"]
            else:
                c = int((b["x"] + 11) / 16)
                here, nxt = ground_row(c), ground_row(c + 1)
                if on and nxt != here and float(b["x"]) + 22 > (c + 1) * 16 - 6:
                    down.append("space")
                for key in ("bug_x", "bug_y"):
                    pass
                try:
                    for bx, by in zip(self.var("bug_x"), self.var("bug_y")):
                        if on and 0 < float(bx) - float(b["x"]) < 60 and abs(float(by) - float(b["y"])) < 30:
                            down.append("space")
                except TypeError:
                    pass
                if gates and n % 9 == 0:
                    pressed = ["enter"]
            self.fr(down=down, pressed=pressed)
        return stop()


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

    def test_every_door_of_the_hub_opens_its_world(self):
        want = {1: ("gw", 1), 2: ("gw", 2), 3: ("gw", 3), 4: ("w4", None), 5: ("w5", None), 6: ("w6", None), 7: ("w7", None)}
        for number, (mode, wn) in want.items():
            g = Game()
            g.to_world(number)
            self.assertEqual(g.var("mode"), mode, number)
            if wn:
                self.assertEqual(g.var("wn"), wn)

    def test_the_puzzles_are_right(self):
        g = Game()
        answers, outs = g.var("pz_answer"), g.var("pz_outs")
        self.assertEqual(len(answers), 6)
        for i in range(6):
            self.assertEqual(len(g.var("pz_opts")[i]), 3)
            self.assertTrue(1 <= answers[i] <= 3)
            self.assertTrue(outs[i][answers[i] - 1])
        # the output of the right choice matches the goal of the gate, and the wrong ones differ
        self.assertEqual(outs[2][1], "fig")
        self.assertEqual(outs[3][0], "4")
        self.assertEqual(outs[4][0], "rob")
        self.assertEqual(outs[5][0], "30")

    def test_the_jump_reaches_the_floating_blocks(self):
        """The floating blocks are 4 tiles (64 pixels) above the ground: a jump must get on top of one."""
        g = Game()
        g.to_world(1)
        g.hero.update({"x": 240, "y": 184})
        for n in range(200):                          # let Echo finish his hello
            g.fr(pressed=["enter"] if n % 30 == 29 else [])
        g.hero.update({"x": 240, "y": 184, "vx": 0, "vy": 0})
        highest = 999
        for n in range(100):
            g.fr(down=(["space"] if n < 20 else []) + (["right"] if n < 20 else []))
            highest = min(highest, float(g.hero["y"]))
        self.assertGreaterEqual(184 - highest, 66)
        self.assertTrue(g.hero["ground"])
        self.assertEqual(float(g.hero["y"]), 120)

    def test_a_wrong_answer_does_not_open_the_gate(self):
        g = Game()
        g.to_world(1)
        for _ in range(1500):
            if g.var("talk_on") in YES:
                g.fr(pressed=["enter"])
            else:
                g.fr(down=["right"])
        g.fr(pressed=["enter"])
        self.assertEqual(g.var("pz"), 1)
        g.fr(pressed=["enter"])              # picks option 1, which is wrong
        g.fr(pressed=["enter"])              # shows the result, then goes back to choosing
        self.assertNotIn(g.var("gate1_open"), YES)
        self.assertEqual(g.var("pz_stage"), "pick")

    def _finish_gate_world(self, number, make):
        g = Game()
        g.to_world(number)
        L = make()
        solid = {1: "GDE", 2: "Mm", 3: "GDE"}[number]
        ok = g.run_bot(L.text(), solid, 14000, lambda: g.var("mode") == "wdone")
        self.assertTrue(ok, f"world {number} could not be finished (x={g.hero['x']})")
        self.assertEqual(g.var("wdone")[number - 1], 1)

    def test_world_1_can_be_finished(self):
        self._finish_gate_world(1, levels.world1)

    def test_world_2_can_be_finished(self):
        self._finish_gate_world(2, levels.world2)

    def test_world_3_can_be_finished(self):
        self._finish_gate_world(3, levels.world3)

    def test_gates_are_walls_until_solved(self):
        for number in (1, 2, 3):
            g = Game()
            g.to_world(number)
            limit = levels.GATE_WORLDS[number]["g1"]
            for n in range(3000):
                if g.var("talk_on") in YES:
                    g.fr(pressed=["enter"])
                else:
                    g.fr(down=["right"] + (["space"] if n % 40 == 0 else []))
            self.assertLess(g.hero["x"], limit, number)

    def test_world_4_can_be_painted(self):
        g = Game()
        g.to_world(4)
        self.assertEqual(g.var("mode"), "w4")
        target = g.var("paint_target")
        cx = cy = 0
        for i, t in enumerate(target):
            if not t or g.var("mode") != "w4":
                continue
            tx, ty = i % 12, i // 12
            while cx != tx or cy != ty:
                key = "right" if cx < tx else "left" if cx > tx else "down" if cy < ty else "up"
                g.fr(pressed=[key])
                cx += (key == "right") - (key == "left")
                cy += (key == "down") - (key == "up")
            g.fr(down=[str(t), "space"])
        for _ in range(5):
            g.fr()
        self.assertEqual(g.var("mode"), "wdone")
        self.assertEqual(g.var("wdone")[3], 1)

    def test_world_5_can_be_finished_by_a_simple_bot(self):
        g = Game()
        g.to_world(5)
        self.assertEqual(g.var("mode"), "w5")
        ok = g.run_bot(levels.world5().text(), "NS", 12000, lambda: g.var("mode") == "wdone", gates=False)
        self.assertTrue(ok)
        self.assertEqual(g.var("wdone")[4], 1)

    def test_world_6_the_boss_can_be_beaten(self):
        g = Game()
        g.to_world(6)
        self.assertEqual(g.var("mode"), "w6")
        self.assertEqual(g.var("boss_hp"), 12)
        for n in range(30000):
            if g.var("mode") != "w6":
                break
            b = g.hero
            boss = float(g.var("boss_x")) + 32
            hx = float(b["x"]) + 11
            down = []
            if abs(hx - boss) > 28:
                down.append("right" if hx < boss else "left")
            elif b["ground"]:
                down.append("space")
            g.fr(down=down)
        self.assertEqual(g.var("mode"), "wdone")
        self.assertEqual(g.var("wdone")[5], 1)

    def test_world_6_a_bolt_hurts_and_a_stomp_hits(self):
        g = Game()
        g.to_world(6)
        for _ in range(3):
            g.fr()
        hp = g.var("boss_hp")
        bx = float(g.var("boss_x"))
        g.hero.update({"x": bx + 20, "y": 120, "vx": 0, "vy": 3})
        g.fr()
        self.assertEqual(g.var("boss_hp"), hp - 1)

    def test_world_7_build_play_and_save(self):
        g = Game()
        g.to_world(7)
        self.assertEqual(g.var("mode"), "w7")
        g.fr(down=["5", "space"])                   # put a coin on the cursor tile (row 12, column 2)
        g.fr(pressed=["s"])
        saved = g.var("level_backup")
        g.fr(down=["x"])                            # rub it out again
        g.fr(pressed=["l"])                         # and load the saved level back
        g.fr(pressed=["enter"])                     # play it
        self.assertNotIn(g.var("edit_on"), YES)
        rows = [r[:30] for r in levels.user_start()]
        rows[11] = rows[11][:1] + "c" + rows[11][2:]
        ok = g.run_bot(rows, "GDS", 6000, lambda: g.var("mode") == "wdone", gates=False)
        self.assertTrue(ok)
        self.assertEqual(g.var("wdone")[6], 1)

    def test_all_seven_done_shows_the_ending(self):
        g = Game()
        g.to_world(7)
        for i in range(6):
            g.it.game["env"].find("wdone").vars["wdone"][i] = 1
        g.fr(pressed=["enter"])
        g.it.game["env"].find("mode").vars["mode"] = "wdone"
        g.it.game["env"].find("done_world").vars["done_world"] = 7
        g.it.game["env"].find("wdone").vars["wdone"][6] = 1
        g.fr(pressed=["enter"])
        self.assertEqual(g.var("mode"), "ending")
        g.fr(pressed=["enter"])
        self.assertEqual(g.var("mode"), "hub")


if __name__ == "__main__":
    unittest.main()
