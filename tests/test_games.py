"""Every game in games/ must be listed, must run, and must reach the ending its test run says it does."""
import json
import os
import unittest

from humanlang.interpreter import Interpreter
from humanlang.errors import HLError

ROOT = os.path.join(os.path.dirname(__file__), "..")
GAMES = os.path.join(ROOT, "games")


def play(code, answers):
    out, queue = [], list(answers)
    Interpreter(out=out.append, inp=lambda prompt: queue.pop(0)).run(code)
    return "".join(out), queue


class Games(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(GAMES, "index.json"), encoding="utf-8") as f:
            self.index = json.load(f)

    def test_every_listed_game_has_its_fields_and_file(self):
        ids = set()
        for g in self.index:
            for key in ("id", "title", "file", "tagline"):
                self.assertTrue(g.get(key), f"{g.get('id')}: missing {key}")
            self.assertNotIn(g["id"], ids)
            ids.add(g["id"])
            self.assertTrue(os.path.isfile(os.path.join(GAMES, g["file"])))

    def test_every_game_file_is_listed(self):
        listed = {g["file"] for g in self.index}
        files = {f for f in os.listdir(GAMES) if f.endswith(".hum")}
        self.assertEqual(files, listed)

    def test_each_test_run_reaches_its_ending_and_uses_every_answer(self):
        for g in self.index:
            with open(os.path.join(GAMES, g["file"]), encoding="utf-8") as f:
                code = f.read()
            for r in g.get("test_runs", []):
                with self.subTest(game=g["id"], ending=r["ending"]):
                    try:
                        text, left = play(code, r["answers"])
                    except HLError as e:
                        self.fail(e.format(code.splitlines()))
                    self.assertIn("ENDING: " + r["ending"], text, text[-300:])
                    self.assertEqual(left, [], "the game did not ask for every answer")


if __name__ == "__main__":
    unittest.main()
