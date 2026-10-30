"""Speed benchmarks for the HumanLang interpreter.  Run: python tools/bench.py [repeats]

Reports the best time of several runs for each program (lower is better).
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.setrecursionlimit(100000)
from humanlang.interpreter import Interpreter  # noqa: E402

PROGRAMS = {
    "fib(23) recursive calls": '''
define fib with n
    if n is less than 2
        give back n
    give back (fib with (n - 1)) + (fib with (n - 2))
set r to fib with 23
''',
    "loop 300k with maths": '''
set total to 0
set i to 0
repeat while i is less than 300000
    add i * 2 mod 7 to total
    add 1 to i
''',
    "nested loops 400x400": '''
set count to 0
repeat 400 times
    repeat 400 times
        add 1 to count
''',
    "lists: build 40k, sum": '''
set things to empty list
repeat 40000 times
    add 3 to things
set total to 0
for each x in things
    add x to total
''',
    "text: 20k joins": '''
set s to ""
repeat 20000 times
    set s to s + "ab"
set n to length of s
''',
    "strings with {braces} 30k": '''
set name to "Sam"
set k to 0
repeat 30000 times
    set line to "Hi {name}, number {k}"
    add 1 to k
''',
}


def run_once(src):
    it = Interpreter(out=lambda s: None)
    t = time.perf_counter()
    it.run(src)
    return time.perf_counter() - t


def main():
    repeats = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    total = 0.0
    for name, src in PROGRAMS.items():
        best = min(run_once(src) for _ in range(repeats))
        total += best
        print(f"{name:32s} {best * 1000:8.0f} ms")
    print(f"{'TOTAL':32s} {total * 1000:8.0f} ms")


if __name__ == "__main__":
    main()
