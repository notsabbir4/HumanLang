import unittest

from humanlang.interpreter import Interpreter

GAME = '''make a sprite called hero
    where "g" is green
    "gg"
    "gg"
make a map called level with tile size 16
    where "#" is blue
    "..........#"
    "..........#"
    "..........#"
    "###########"
make a body called hero at 20, 0 with size 8 by 8
play a game titled "T" with size 176 by 64
    every frame
        make the body hero run right
        update the body hero on the map level with solid "#"
        draw the map level
        draw the sprite hero at the body hero
'''


def play(src, frames, keys=()):
    it = Interpreter(out=lambda t: None)
    it.run(src)
    for _ in range(frames):
        it.game_frame(down=keys)
    return it


class PhysicsTests(unittest.TestCase):
    def test_falls_lands_and_runs_into_wall(self):
        it = play(GAME, 120)
        b = it.bodies["hero"]
        self.assertTrue(b["ground"])
        self.assertEqual(b["y"], 64 - 16 - 8)       # standing on the floor row
        self.assertEqual(b["x"], 160 - 8)           # stopped by the wall at column 11

    def test_jump_only_from_ground(self):
        src = GAME.replace("make the body hero run right", "make the body hero stop\n        make the body hero jump")
        it = play(src, 1)
        self.assertEqual(it.bodies["hero"]["vy"] > -1, True)   # still in the air at frame 1: not on the ground yet
        it = play(src, 120)
        self.assertGreater(it.bodies["hero"]["y"], 0)

    def test_expressions(self):
        src = GAME.replace("draw the map level", 'draw the map level\n        if the body hero is on the ground\n            say "ground {the x of the body hero}"')
        out = []
        it = Interpreter(out=out.append)
        it.run(src)
        for _ in range(100):
            it.game_frame()
        self.assertTrue(any(o.startswith("ground ") for o in out))

    def test_unknown_body(self):
        it = Interpreter(out=lambda t: None)
        with self.assertRaises(Exception) as c:
            it.run(GAME.replace("update the body hero", "update the body her"))
            it.game_frame()
        self.assertIn("body", str(c.exception).lower())


if __name__ == "__main__":
    unittest.main()
