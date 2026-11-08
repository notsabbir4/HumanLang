import os
import tempfile
import unittest
from humanlang.interpreter import Interpreter
from humanlang.memory import Memory


def run(src, memory):
    out = []
    Interpreter(out=out.append, memory=memory).run(src)
    return "".join(out).strip()


class MemoryTests(unittest.TestCase):
    def test_remember_across_runs(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "m.json")
            prog = "set n to recall n\nif n is nothing\n    set n to 0\nadd 1 to n\nremember n\nsay n"
            for expect in ("1", "2", "3"):
                m = Memory(path=path)
                self.assertEqual(run(prog, m), expect)
                m.save()

    def test_snapshot_and_changes(self):
        m = Memory('{"a": 5}')
        self.assertIsNone(m.take_changes())
        run('remember 7 as "a"', m)
        self.assertIn("7", m.take_changes())
        self.assertIsNone(m.take_changes())

    def test_forget_and_limits(self):
        m = Memory()
        run('remember 1 as "x"\nforget "x"\nsay recall "x"', m)
        self.assertIsNone(m.recall("x"))
        with self.assertRaises(Exception):
            run('remember 1 as ""', m)


if __name__ == "__main__":
    unittest.main()
