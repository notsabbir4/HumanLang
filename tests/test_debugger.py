import unittest

from humanlang.debugger import explain, record


class DebuggerTests(unittest.TestCase):
    def test_records_each_line_with_variables(self):
        r = record('set total to 0\nfor each n from 1 to 3\n    add n to total\nsay "Total: {total}"')
        lines = [s["line"] for s in r["steps"]]
        self.assertEqual(lines, [1, 2, 3, 3, 3, 4])
        self.assertEqual(r["steps"][-1]["vars"]["total"], "6")
        self.assertEqual(r["output"], "Total: 6\n")
        self.assertIsNone(r["error"])

    def test_error_is_reported_with_steps_before_it(self):
        r = record("set a to 1\nsay a + oops")
        self.assertEqual(len(r["steps"]), 2)
        self.assertIn("oops", r["error"])

    def test_truncates(self):
        r = record("repeat 100000 times\n    set x to 1", max_steps=50)
        self.assertTrue(r["truncated"])
        self.assertEqual(len(r["steps"]), 50)

    def test_explain(self):
        self.assertIn("stores the answer in x", explain("set x to 5"))
        self.assertEqual(explain("zzz"), "Runs this line.")


if __name__ == "__main__":
    unittest.main()
