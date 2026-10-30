"""Fuzzer: no input may ever crash HL with a raw Python exception.
Only HLError is acceptable. Run: python tests/fuzz.py [iterations] [seed]"""
import glob, os, random, sys, time, traceback
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.setrecursionlimit(50000)
from humanlang.errors import HLError
from humanlang.interpreter import Interpreter

ROOT = os.path.join(os.path.dirname(__file__), "..")
WORDS = ("say set change add subtract remove ask if otherwise repeat while for each in define with give back stop skip "
         "use try that fails write file to from of and or not is less greater than at least most yes no nothing list "
         "item items how many times plus minus divided by mod then number text length uppercase random square root "
         "math files dates print else true null return break by contains split join replace trim sorted reversed sum largest smallest pick the date today now power x y name naïve 名前 é ✓ ½ ٣ $ @ ; : = < > ! 0 1 3 2.5 -1 \"hi\" \"{x}\" \"{\" ( ) , + - * / % empty").split()

class Timeout(Exception): pass

def attempt(src):
    out = []
    it = Interpreter(out=lambda s: out.append(s) if sum(map(len, out)) < 10000 else None,
                     inp=lambda p: "5")
    deadline = time.monotonic() + 1.0

    def watch(line, text):  # runs before every statement, so endless loops are cut off on any system
        if time.monotonic() > deadline:
            raise Timeout()
    it.trace = watch
    try:
        it.run(src)
    except HLError:
        pass
    except Timeout:
        pass  # infinite loops are legal programs

def mutate(src, rnd):
    toks = src.split(" ")
    for _ in range(rnd.randint(1, 4)):
        op = rnd.choice("dri s")
        i = rnd.randrange(len(toks))
        if op == "d": toks.pop(i) if len(toks) > 1 else None
        elif op == "r": toks[i] = rnd.choice(WORDS)
        elif op == "i": toks.insert(i, rnd.choice(WORDS))
        else:
            j = rnd.randrange(len(toks)); toks[i], toks[j] = toks[j], toks[i]
    s = " ".join(toks)
    if rnd.random() < .2 and s: k = rnd.randrange(len(s)); s = s[:k] + rnd.choice('"{}\t\n ()') + s[k:]
    return s

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rnd = random.Random(seed)
    seeds = [open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ROOT, "examples", "*.hum"))]
    bad = {}
    for k in range(n):
        if rnd.random() < .7: src = mutate(rnd.choice(seeds), rnd)
        else: src = "\n".join(" ".join(rnd.choice(WORDS) for _ in range(rnd.randint(1, 8))) for _ in range(rnd.randint(1, 4)))
        try: attempt(src)
        except Exception as e:
            key = f"{type(e).__name__}: {e}".split("\n")[0][:100]
            bad.setdefault(key, (src, traceback.format_exc()))
    print(f"{n} inputs, {len(bad)} distinct crash(es)")
    for key, (src, tb) in bad.items():
        print("\n=== ", key); print(repr(src)[:300]); print(tb.strip().splitlines()[-3])
    return 1 if bad else 0
sys.exit(main())
