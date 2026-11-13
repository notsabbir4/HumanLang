"""The course's thinking (website/static/learn-core.js) is plain JavaScript: test it with node on the real course data."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "website"))
import beginner  # noqa: E402


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class LearnCore(unittest.TestCase):
    def test_core(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "data.json")
            with open(path, "w", encoding="utf8") as f:
                f.write(beginner.export_json(lambda t: ("<p></p>", []), lambda c: c))
            r = subprocess.run(["node", os.path.join(ROOT, "tests", "learn_core_test.js"), path], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sound(self):
        r = subprocess.run(["node", os.path.join(ROOT, "tests", "learn_sound_test.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
