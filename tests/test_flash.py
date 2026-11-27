"""HL v0.6.2 - Flash: the fast path must give exactly the same answers and the same messages as the plain walk."""
import unittest

from humanlang.errors import HLError
from humanlang.interpreter import Interpreter

PROGRAM = '''
set total to 0
set xs to list of 3, 1.5, 4, 1, 5
define pick with i
    if i is greater than 2 and i is less than 5 or i is 1
        give back item i of xs
    give back 0 - i
for each k from 1 to 5
    set v to pick with k
    add v * 2 + 1 to total
    if not (v is 4)
        add 1 to total
say total
say "{total} and {item 2 of xs + 0.5}"
repeat 3 times
    set total to total - 1
say total
'''


def run(code, trace=False):
    out = []
    it = Interpreter(out=out.append)
    if trace:
        it.trace = lambda *a: None          # watching turns the fast path off
    try:
        it.run(code)
    except HLError as e:
        return "".join(out) + "ERR " + str(e) + " @" + str(e.line)
    return "".join(out)


class Flash(unittest.TestCase):
    def test_same_results_fast_and_plain(self):
        self.assertEqual(run(PROGRAM), run(PROGRAM, trace=True))
        self.assertTrue(run(PROGRAM).strip())

    def test_same_mistakes(self):
        for bad in ('set a to 1\nrepeat 3 times\n    set b to a + "x"\n',
                    'set xs to list of 1, 2\nrepeat 3 times\n    say item 5 of xs\n',
                    'repeat 3 times\n    say nothere + 1\n',
                    'set a to 2\nrepeat 3 times\n    if a is less than "x"\n        say 1\n'):
            self.assertEqual(run(bad), run(bad, trace=True))
            self.assertIn("ERR", run(bad))

    def test_the_second_run_uses_the_fast_copy(self):
        it = Interpreter()
        it.run("define f with a\n    give back a + 1\nrepeat 3 times\n    set z to f with 2\n")
        self.assertTrue(any(c[1] is not None for c in it._fast.values()))


if __name__ == "__main__":
    unittest.main()
