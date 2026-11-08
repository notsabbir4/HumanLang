import unittest
from decimal import Decimal
from humanlang.formula import evaluate, FormulaError
from humanlang.interpreter import Interpreter


def run(src):
    out = []
    Interpreter(out=out.append).run(src)
    return "".join(out).strip()


class FormulaTests(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(evaluate("2 * (3 + 4)"), 14)
        self.assertEqual(evaluate("2 + 3 * 4"), 14)
        self.assertEqual(evaluate("-2^2"), -4)
        self.assertEqual(evaluate("2^3^2"), 512)
        self.assertEqual(evaluate("(1+2)(3+4)"), 21)

    def test_extras(self):
        self.assertEqual(evaluate("50%"), Decimal("0.5"))
        self.assertEqual(evaluate("5!"), 120)
        self.assertEqual(evaluate("max(1,5,3)"), 5)
        self.assertEqual(evaluate("sqrt(16)"), 4)
        self.assertEqual(evaluate("sin(90)"), 1)

    def test_errors(self):
        for bad in ("2 +", "1/0", "(1", "foo(2)", "import os"):
            with self.assertRaises(FormulaError):
                evaluate(bad)

    def test_in_hl(self):
        self.assertEqual(run('say calculate "2 * (3 + 4)"'), "14")

    def test_hl_error_is_catchable(self):
        out = run('try\n    say calculate "2 +"\nif that fails\n    say "bad"')
        self.assertEqual(out, "bad")


if __name__ == "__main__":
    unittest.main()
