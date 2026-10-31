"""Differential checks for the stress programs: HumanLang's answers are compared with Python's.
Run from the project folder:  python stress/run_checks.py
"""
import math
import os
import random
import re
import subprocess
import sys
import tempfile
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV = dict(os.environ, PYTHONPATH=ROOT)


def hl(program, lines, cwd=None):
    out = subprocess.run([sys.executable, "-m", "humanlang", "run", os.path.join(HERE, program)],
                         input="\n".join(lines) + "\n", capture_output=True, text=True, cwd=cwd or ROOT, env=ENV)
    return out.stdout


# ---------------- 1. calculator ----------------
def gen(d=0):
    r = random.random()
    if d > 3 or r < 0.3:
        return random.choice([str(random.randint(0, 20)), f"{random.randint(0, 9)}.{random.randint(1, 9)}"])
    if r < 0.45:
        return "(" + gen(d + 1) + ")"
    if r < 0.55:
        return "-" + gen(d + 1)
    op = random.choice(["+", "-", "*", "/", "%", "^", "+", "-", "*"])
    a, b = gen(d + 1), gen(d + 1)
    if op == "^":
        b = str(random.randint(0, 3)) if random.random() < .7 else "(" + b + ")"
    sp = random.choice(["", " "])
    return f"{a}{sp}{op}{sp}{b}"


def check_calculator(n=400):
    random.seed(11)
    exprs = [gen() for _ in range(n)]
    out = hl("calc.hum", exprs + ["quit"])
    answers = re.findall(r">\s+([^\n]*)\n", out)
    bad = 0
    for e, got in zip(exprs, answers):
        try:
            want = eval(e.replace("^", "**"))
        except ZeroDivisionError:
            want = "ERR"
        except OverflowError:
            continue
        if isinstance(want, complex):
            continue
        good = got.startswith("Error") if want == "ERR" else _close(got, want)
        if not good:
            bad += 1
            print("  calculator mismatch:", e, "HL:", got, "Python:", want)
    return len(exprs), bad


def _close(got, want):
    try:
        return math.isclose(float(got), float(want), rel_tol=1e-8, abs_tol=1e-9)
    except ValueError:
        return False


# ---------------- 2. grades ----------------
def r2(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def letter(a):
    return "A" if a >= 90 else "B" if a >= 80 else "C" if a >= 70 else "D" if a >= 60 else "F"


def check_grades(sessions=60):
    random.seed(5)
    bad = 0
    for _ in range(sessions):
        names, marks, inp = [], {}, []
        pool = ["Ana", "Bo", "Cy", "Di", "Eli", "Fay", "Gus"]
        for _ in range(random.randint(5, 25)):
            c = random.choice([1, 1, 2, 2, 2, 2, 6, 3])
            if c == 1:
                n = random.choice(pool)
                if random.random() < .2:
                    n = n.upper()
                inp += ["1", n]
                if n.lower() not in [x.lower() for x in names]:
                    names.append(n)
                    marks[n.lower()] = []
            elif c == 2 and names:
                n = random.choice(names + ["Nobody"])
                if random.random() < .3:
                    n = n.lower()
                m = random.choice([random.randint(0, 100), round(random.uniform(0, 100), 1)])
                inp += ["2", n]
                if n.lower() in marks:
                    if random.random() < .2:
                        inp += ["150"]
                    inp += [str(m)]
                    marks[n.lower()].append(m)
            elif c == 6 and names:
                n = random.choice(names)
                inp += ["6", n]
                names = [x for x in names if x != n]
                marks.pop(n.lower())
        out = hl("grades.hum", inp + ["3", "4", "0"])
        got = {r[0]: r for r in re.findall(r"^(\S+)\s+(\d+)\s+(\S+)\s+(\S+)$", out, re.M)}
        avgs = []
        for n in names:
            ms, r = marks[n.lower()], got.get(n)
            if not ms:
                ok = bool(r) and r[1] == "0"
            else:
                a = r2(sum(ms) / len(ms))
                avgs.append(a)
                ok = bool(r) and int(r[1]) == len(ms) and abs(float(r[2]) - a) < 1e-9 and r[3] == letter(a)
            if not ok:
                bad += 1
                print("  grades row mismatch:", n, ms, r)
        if avgs:
            m = re.search(r"Class average: (\S+)", out)
            if not m or abs(float(m.group(1)) - r2(sum(avgs) / len(avgs))) > 1e-9:
                bad += 1
                print("  grades class average mismatch")
            rank = [float(x) for x in re.findall(r"\d+\. \S+ - (\S+)\n", out)]
            if rank != sorted(rank, reverse=True) or sorted(rank) != sorted(avgs):
                bad += 1
                print("  grades ranking mismatch", rank)
    return sessions, bad


# ---------------- 3. contacts (three separate runs share one file) ----------------
def check_contacts(trials=25):
    random.seed(21)
    names = ["Ann", "ann", "Bob Li", "Zoe~Q", "Émile", "élodie", "Zed", "Carla Ruiz", "D'Arcy", "Mo"]
    bad = 0
    with tempfile.TemporaryDirectory() as folder:
        for _ in range(trials):
            path = os.path.join(folder, "contacts.txt")
            if os.path.exists(path):
                os.remove(path)
            model = {}
            for _ in range(3):
                inp = []
                for _ in range(random.randint(3, 10)):
                    op = random.choice(["add", "add", "add", "update", "delete", "search"])
                    n = random.choice(names)
                    if op == "add":
                        ph = random.choice(["12345", "+1 (555) 010-2000", "555-0101", "12", "abc12"])
                        em = random.choice(["", "a@b.co", "bad", "x@y"])
                        inp += ["add", n, ph, em]
                        ok_ph = len(ph) >= 5 and all(c in "0123456789+-() " for c in ph)
                        ok_em = em == "" or (em.count("@") == 1 and not em.startswith("@")
                                             and "." in em.split("@")[1] and " " not in em)
                        if n.lower() not in model and ok_ph and ok_em:
                            model[n.lower()] = (n, ph, em)
                    elif op == "update":
                        ph = random.choice(["", "99999", "+44 20 7946 0000", "x"])
                        em = random.choice(["", "n@e.org"])
                        inp += ["update", n]
                        if n.lower() in model:
                            old = model[n.lower()]
                            newph = ph or old[1]
                            if len(newph) >= 5 and all(c in "0123456789+-() " for c in newph):
                                inp += [ph, em]
                                model[n.lower()] = (old[0], newph, em or old[2])
                            else:
                                inp += [ph]  # a bad phone stops the update before the email question
                    elif op == "delete":
                        ans = random.choice(["yes", "no"])
                        inp += ["delete", n]
                        if n.lower() in model:
                            inp += [ans]
                            if ans == "yes":
                                del model[n.lower()]
                out = hl("contacts.hum", inp + ["list", "quit"], cwd=folder)
                tail = out.split("contact(s).")[0].split("[add / list / search / update / delete / quit]")[-1]
                shown = [tuple(x) for x in re.findall(r"^\s*(.*?)  \|  (.*?)  \|  (.*)$", tail, re.M)]
                expect = sorted(model.values(), key=lambda t: t[0].lower())
                if shown != [tuple(x) for x in expect] and not (not model and "empty" in out):
                    bad += 1
                    print("  contacts listing mismatch:", expect, shown)
                    break
            if os.path.exists(path):
                rows = sorted(line for line in open(path, encoding="utf-8").read().split("\n")[1:] if line)
                if rows != sorted("|".join(v) for v in model.values()):
                    bad += 1
                    print("  contacts file mismatch")
    return trials, bad


if __name__ == "__main__":
    total_bad = 0
    for label, fn in (("calculator: random expressions", check_calculator),
                      ("grades: random sessions", check_grades),
                      ("contacts: random multi-run sessions", check_contacts)):
        n, bad = fn()
        total_bad += bad
        print(f"{label}: {n} cases, {bad} disagreements with Python")
    sys.exit(1 if total_bad else 0)
