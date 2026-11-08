import os
import tempfile
import unittest

from humanlang.assets import data_urls, kind_of, scan_folder
from humanlang.gamepage import game_to_html
from humanlang.interpreter import Interpreter

GAME = '''play a game titled "A" with size 100 by 80
    when the game starts
        play the music "adventure"
    every frame
        draw the picture "face.png" at 1, 2 with size 10 by 10
    when the key "space" is pressed
        play the sound "boom.wav"
        stop the music
'''


class AssetTests(unittest.TestCase):
    def folder(self):
        d = tempfile.mkdtemp()
        for n in ("face.png", "boom.wav", "notes.txt"):
            with open(os.path.join(d, n), "wb") as f:
                f.write(b"x")
        return d

    def test_scan_and_kinds(self):
        d = self.folder()
        self.assertEqual(scan_folder(d), {"boom.wav": "audio", "face.png": "picture"})
        self.assertEqual(scan_folder(d, 'draw the picture "face.png"'), {"face.png": "picture"})
        self.assertIsNone(kind_of("a.txt"))
        self.assertTrue(data_urls(d, ["face.png"])["face.png"].startswith("data:image/png;base64,"))

    def test_game_uses_files(self):
        it = Interpreter(out=lambda t: None)
        it.assets = {"face.png": "picture", "boom.wav": "audio"}
        it.run(GAME)
        f = it.game_frame()
        self.assertEqual(f["cmds"][0], ["picture", "face.png", 1, 2, 10, 10])
        self.assertEqual(f["music"], "adventure")
        f = it.game_frame(pressed=["space"])
        self.assertEqual(f["sounds"], ["boom.wav"])
        self.assertEqual(f["music"], "")

    def test_missing_picture_is_friendly(self):
        it = Interpreter(out=lambda t: None)
        it.run(GAME)
        with self.assertRaises(Exception) as c:
            it.game_frame()
        self.assertIn("picture called", str(c.exception))

    def test_build_embeds_files(self):
        d = self.folder()
        html = game_to_html(GAME, "A", folder=d)
        self.assertIn("data:image/png;base64", html)
        self.assertNotIn("\"notes.txt\":", html)


if __name__ == "__main__":
    unittest.main()
