"""Round 2, test 6: deliberately wrong programs. Each is run with `hl run`; we look for Python crashes (a traceback),
hangs, and messages that don't help. Run from the project folder:  python stress/breaking.py"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV = dict(os.environ, PYTHONPATH=ROOT)

CASES = [
    # (name, program text, stdin lines)
    ("typo in a name", 'set name to "Sam"\nsay "Hi {nmae}"', []),
    ("unknown word at line start", 'print "hi"', []),
    ("missing quote", 'say "hello', []),
    ("missing bracket", 'say "a {1 + "', []),
    ("unclosed bracket in expression", "set x to (1 + 2\nsay x", []),
    ("tab indent", "if yes\n\tsay 1", []),
    ("odd indent", "if yes\n   say 1", []),
    ("indent too deep", "say 1\n        say 2", []),
    ("else without if", "otherwise\n    say 1", []),
    ("if without body", "if yes\nsay 2", []),
    ("add text and number", 'say "a" + 1', []),
    ("divide by zero", "say 1 / 0", []),
    ("modulo zero", "say 5 % 0", []),
    ("item 0", "set l to list of 1, 2\nsay item 0 of l", []),
    ("item past end", "set l to list of 1, 2\nsay item 3 of l", []),
    ("item of empty", "say item 1 of empty list", []),
    ("negative item", "set l to list of 1\nsay item -1 of l", []),
    ("item 1.5", "set l to list of 1, 2\nsay item 1.5 of l", []),
    ("item of a number", "set n to 5\nsay item 1 of n", []),
    ("length of number", "say length of 5", []),
    ("compare text and number", 'if "a" is less than 1\n    say 1', []),
    ("compare lists", "if (list of 1) is less than (list of 2)\n    say 1", []),
    ("not on a number", "say not 5", []),
    ("if on a number", "if 1\n    say 1", []),
    ("repeat -1 times", "repeat -1 times\n    say 1\nsay 2", []),
    ("repeat 2.5 times", "repeat 2.5 times\n    say 1", []),
    ("repeat text times", 'repeat "a" times\n    say 1', []),
    ("undefined function", "say nosuch with 1", []),
    ("too few arguments", "define f with a and b\n    give back a\nsay f with 1", []),
    ("too many arguments", "define f with a\n    give back a\nsay f with 1 and 2", []),
    ("give back outside function", "give back 5", []),
    ("stop outside loop", "stop", []),
    ("skip outside loop", "skip", []),
    ("use unknown module", "use banana", []),
    ("math without use", "say square root of 4", []),
    ("sqrt of negative", "use math\nsay square root of -4", []),
    ("number of bad text", 'say number of "abc"', []),
    ("split by empty", 'use text\nsay split "abc" by ""', []),
    ("replace empty old", 'use text\nsay replace "" by "x" in "abc"', []),
    ("huge power", "say 10 to the power of 100000", []),
    ("huge float", "say 10.5 to the power of 1000", []),
    ("power negative", "say 0 to the power of -1", []),
    ("big factorial recursion", "define f with n\n    give back n * f with (n - 1)\nsay f with 5", []),
    ("recursion forever", "define f with n\n    give back f with (n + 1)\nsay f with 1", []),
    ("infinite loop (killed at 10s)", "repeat while yes\n    set x to 1", []),
    ("endless output", 'repeat while yes\n    say "spam"', []),
    ("memory: list doubling", "set l to list of 1\nrepeat 40 times\n    set l to l + l\nsay how many items in l", []),
    ("memory: text doubling", 'set t to "ab"\nrepeat 60 times\n    set t to t + t\nsay length of t', []),
    ("read missing file", 'use files\nsay read file "nope.txt"', []),
    ("write to bad path", 'use files\nwrite "x" to file "/no/such/dir/x.txt"', []),
    ("read a binary file", 'use files\nsay length of (read file "/bin/ls")', []),
    ("ask number gets text then number", 'ask number "n?" and save it as n\nsay n + 1', ["abc", "", "4"]),
    ("ask number: input ends", 'ask number "n?" and save it as n\nsay n', ["abc"]),
    ("ask text: input ends", 'ask "name?" and save it as n\nsay n', []),
    ("ask number: 1e3, 0x10, -0, 5.", 'ask number "n?" and save it as n\nsay n', ["1e3", "0x10", "-0", "5.", "7"]),
    ("ask number: 'nan' and 'inf'", 'ask number "n?" and save it as n\nsay n', ["nan", "inf", "-inf", "3"]),
    ("ask number: huge", 'ask number "n?" and save it as n\nsay n * n', ["9" * 400]),
    ("empty program", "", []),
    ("only comments", "note: nothing here\nnote: still nothing", []),
    ("no trailing newline", 'say "x"', []),
    ("windows line endings", 'say "a"\r\nsay "b"\r\n', []),
    ("byte-order mark", '﻿say "bom"', []),
    ("null byte in text", 'say "a\x00b"', []),
    ("emoji and rtl text", 'set s to "hi \U0001F600 שלום"\nsay length of s\nsay reversed of s', []),
    ("very long line", 'say "' + "x" * 200000 + '"', []),
    ("1000 nested brackets", "say " + "(" * 1000 + "1" + ")" * 1000, []),
    ("200 nested ifs", "".join("    " * i + "if yes\n" for i in range(200)) + "    " * 200 + "say 1", []),
    ("name that is a reserved word", "set list to 5", []),
    ("name with a space or symbol", "set my-name to 5", []),
    ("name starting with a digit", "set 2x to 5", []),
    ("record: missing field", "set r to record with a 1\nsay field b of r", []),
    ("record: field of a number", "set n to 5\nsay field a of n", []),
    ("change an unset variable", "change x to 5", []),
    ("add to an unset variable", "add 1 to total", []),
    ("add number to text variable", 'set t to "a"\nadd 1 to t', []),
    ("join list with numbers", 'use text\nsay join (list of 1, 2) by ","', []),
    ("sorted mixed list", 'say sorted of (list of 1, "a", 2)', []),
    ("sorted by missing field", "say sorted of (list of (record with a 1), (record with b 2)) by field a", []),
    ("largest of empty", "use math\nsay largest of empty list", []),
    ("sum of text list", 'use math\nsay sum of (list of "a", "b")', []),
    ("random range backwards", "use random\nsay random number from 5 to 1", []),
    ("random item of empty", "use random\nsay random item from empty list", []),
    ("fail with a number", "fail with 5", []),
    ("try inside try, problem reused", 'try\n    try\n        say 1 / 0\n    if that fails\n        say "inner {problem}"\n        say item 9 of empty list\nif that fails\n    say "outer {problem}"', []),
    ("stop the program inside try", 'try\n    stop the program\nif that fails\n    say "no"\nsay "after"', []),
]


def run(program, lines):
    path = os.path.join(HERE, "_case.hum")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(program)
    try:
        p = subprocess.run([sys.executable, "-m", "humanlang", "run", path], input="\n".join(lines) + ("\n" if lines else ""),
                           capture_output=True, text=True, cwd=ROOT, env=ENV, timeout=10, errors="replace")
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        return None, (e.stdout or b"")[:200] if isinstance(e.stdout, bytes) else (e.stdout or ""), "", True
    finally:
        os.remove(path)


def main():
    crashes = hangs = 0
    for name, prog, lines in CASES:
        code, out, err, hung = run(prog, lines)
        text = (err or "").strip()
        flag = ""
        if hung:
            flag, hangs = "HANG", hangs + 1
        elif "Traceback" in text or "Error:" in text and "Line " not in text:
            flag, crashes = "CRASH", crashes + 1
        first = (out.strip().splitlines() or [""])[-1][:70] if code == 0 else text.splitlines()[0][:110] if text else ""
        print(f"{flag or ('ok' if code == 0 else 'err'):5} {name:42} exit={code} | {first}")
    print(f"\n{len(CASES)} cases, {crashes} crashes, {hangs} hangs")


if __name__ == "__main__":
    main()
