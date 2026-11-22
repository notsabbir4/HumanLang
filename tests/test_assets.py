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

    def test_continue_the_music_asks_the_screen_to_resume(self):
        it = Interpreter(out=lambda t: None)
        it.assets = {"a.mp3": "audio", "b.mp3": "audio"}
        it.run('play a game titled "T" with size 40 by 40\n    when the key "a" is pressed\n        play the music "b.mp3"\n    when the key "b" is pressed\n        continue the music "a.mp3"\n    every frame\n        draw the sprite x at 0, 0\n'.replace("        draw the sprite x at 0, 0\n","        put a rectangle at 0, 0 with width 4 and height 4 and colour red\n"))
        f = it.game_frame(pressed=["a"])
        self.assertEqual(f["music"], "b.mp3")
        self.assertNotIn("resume", f)
        f = it.game_frame(pressed=["b"])
        self.assertEqual((f["music"], f["resume"]), ("a.mp3", True))

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

    # ---- videos: play the video "intro.mp4" ----
    VIDEO_GAME = '''play a game titled "V" with size 100 by 80
    when the game starts
        play the video "intro.mp4"
        play the music "adventure"
    every frame
        draw the picture "face.png" at 1, 2
'''

    def test_video_files_are_found_and_embedded(self):
        d = tempfile.mkdtemp()
        for n in ("intro.mp4", "clip.webm", "movie.avi"):
            with open(os.path.join(d, n), "wb") as f:
                f.write(b"x")
        self.assertEqual(scan_folder(d), {"clip.webm": "video", "intro.mp4": "video"})
        self.assertEqual(kind_of("A.MP4"), "video")
        self.assertIsNone(kind_of("movie.avi"))
        self.assertTrue(data_urls(d, ["intro.mp4"])["intro.mp4"].startswith("data:video/mp4;base64,"))
        html = game_to_html(self.VIDEO_GAME, "V", folder=d)
        self.assertIn("data:video/mp4;base64", html)
        self.assertIn("data:video", html.split("const KINDS")[1][:200])       # the page tells videos from sounds

    def test_play_the_video_sends_it_to_the_screen_once(self):
        it = Interpreter(out=lambda t: None)
        it.assets = {"intro.mp4": "video", "face.png": "picture"}
        it.run(self.VIDEO_GAME)
        f = it.game_frame()
        self.assertEqual(f["video"], "intro.mp4")
        self.assertEqual(f["music"], "adventure")        # the screen holds the music back until the video ends
        self.assertNotIn("video", it.game_frame())       # only the frame that asked for it carries it

    def test_play_video_without_the_works_too(self):
        it = Interpreter()
        it.assets = {"intro.mp4": "video"}
        it.run('play a game titled "V"\n    every frame\n        play video "intro.mp4"\n')
        it.game_frame()
        self.assertEqual(it.game_frame().get("video"), "intro.mp4")

    def test_missing_video_is_friendly(self):
        it = Interpreter(out=lambda t: None)
        it.assets = {"inro.mp4": "video", "face.png": "picture"}
        it.run(self.VIDEO_GAME)
        with self.assertRaises(Exception) as c:
            it.game_frame()
        self.assertIn('video called "intro.mp4"', str(c.exception))
        self.assertIn("inro.mp4", c.exception.hint)      # it suggests the file that is there
        it = Interpreter(out=lambda t: None)
        it.run(self.VIDEO_GAME)
        with self.assertRaises(Exception) as c:
            it.game_frame()
        self.assertIn("mp4 or webm", c.exception.hint)

    def test_a_picture_is_not_a_video(self):
        it = Interpreter(out=lambda t: None)
        it.assets = {"intro.mp4": "picture", "face.png": "picture"}
        it.run(self.VIDEO_GAME)
        with self.assertRaises(Exception):
            it.game_frame()

    def test_video_statement_is_checked_before_running(self):
        from humanlang.lint import STATEMENTS
        self.assertIn("video", STATEMENTS)
        it = Interpreter(out=lambda t: None)
        with self.assertRaises(Exception) as c:
            it.run('play a game titled "V"\n    every frame\n        play the video\n')
        self.assertIn("play video", c.exception.hint)      # the example in the message


if __name__ == "__main__":
    unittest.main()
