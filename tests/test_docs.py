"""Every runnable code block in docs/*.md must behave exactly as the docs say."""
import glob
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
from docs_runner import find_examples, run_example, transcript  # noqa: E402


class DocExamples(unittest.TestCase):
    def test_docs_exist(self):
        self.assertTrue(glob.glob(os.path.join(ROOT, "docs", "*.md")))

    def test_every_example(self):
        total = 0
        for path in sorted(glob.glob(os.path.join(ROOT, "docs", "*.md"))):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            for ex in find_examples(text):
                total += 1
                where = f"{os.path.basename(path)} line {ex.line}"
                with self.subTest(example=where):
                    out, err = run_example(ex)
                    if ex.kind == "hum-error":
                        self.assertIsNotNone(err, f"{where}: expected an error")
                    else:
                        self.assertIsNone(err, f"{where}: unexpected error\n{err}")
                    if ex.kind != "hum-random":
                        self.assertIsNotNone(ex.out_text, f"{where}: add an output block, then run tools/docs_fill.py")
                        self.assertEqual(transcript(ex), ex.out_text, where)
        self.assertGreater(total, 40)


if __name__ == "__main__":
    unittest.main()
