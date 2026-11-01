"""Round 2 checks. Run from the project folder:  python stress/run_checks_2.py
Test 4 compares csv_report.hum with Python's csv module on random, deliberately nasty CSV files."""
import csv
import io
import os
import re
import random
import subprocess
import sys
import tempfile
import time
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENV = dict(os.environ, PYTHONPATH=ROOT)


def money(x):
    cents = int((Decimal(str(x)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return f"{cents // 100}.{cents % 100:02d}"


def q(v):
    return '"' + v.replace('"', '""') + '"' if any(c in v for c in ',"\n') else v


def model(text, exact=False):
    """What csv_report.hum should print and write."""
    rows = list(csv.reader(io.StringIO(text, newline="")))
    if not rows:
        return "Read 0 rows.\nThe file is empty.\n", None
    out = [f"Read {len(rows)} rows."]
    if [h.strip().lower() for h in rows[0]] != ["date", "region", "product", "units", "price"]:
        return None, None  # the header text is checked elsewhere
    good, bad = [], []
    for n, r in enumerate(rows[1:], 2):
        if r == [] or (len(r) == 1 and r[0] == ""):
            continue
        if len(r) != 5:
            bad.append(f"row {n}: expected 5 columns, found {len(r)}")
            continue
        if exact:  # the exact program accepts only digits (and one point in the price)
            if not re.fullmatch(r"[0-9]+", r[3].strip()):
                bad.append(f"row {n}: units must be a whole number and nothing can be negative")
                continue
            if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", r[4].strip()):
                bad.append(f"row {n}: units or price is not a number")
                continue
            u, p = Decimal(r[3].strip()), Decimal(r[4].strip())
        else:
            try:
                u, p = Decimal(r[3].strip()), Decimal(r[4].strip())
            except Exception:
                bad.append(f"row {n}: units or price is not a number")
                continue
            if u < 0 or p < 0 or u != u.to_integral_value():
                bad.append(f"row {n}: units must be a whole number and nothing can be negative")
                continue
        good.append((r[0].strip(), r[1].strip(), r[2].strip(), u, p))
    out.append(f"{len(good)} good rows, {len(bad)} rejected.")
    out += ["  rejected " + b for b in bad]
    reg, prod, grand = {}, {}, Decimal(0)
    for d, rg, pr, u, p in good:
        amount = u * p
        if exact:  # the exact program rounds each row to whole cents before adding up
            amount = Decimal(money(amount).replace(".", "")) / 100
        reg[rg] = reg.get(rg, 0) + amount
        prod[pr] = prod.get(pr, 0) + u
        grand += amount
    def key(s):  # HL sorts text like a dictionary: no capitals, no accents
        return ("".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).casefold(), s)
    out += ["", "Sales by region"] + [f"  {k}: {money(reg[k])}" for k in sorted(reg, key=key)]
    out += ["Units by product"] + [f"  {k}: {prod[k]}" for k in sorted(prod, key=key)]
    out.append(f"Grand total: {money(grand)}")
    clean = ["date,region,product,units,price,total"] + [
        ",".join([q(d), q(rg), q(pr), str(u), money(p), money(u * p)]) for d, rg, pr, u, p in good]
    return "\n".join(out) + "\n", "\n".join(clean) + "\n"


WORDS = ["Widget", "Gadget", "north", "South", "East, West", 'The "Pro" one', "Émile", "Zoe", "a\nb", "", "  pad  ", "x,y,z", '""']


def make_file():
    lines = ["Date,Region,Product,Units,Price"]
    for _ in range(random.randint(0, 30)):
        r = random.random()
        f = lambda: q(random.choice(WORDS))
        if r < .06:
            lines.append("")
        elif r < .12:
            lines.append(",".join(f() for _ in range(random.choice([1, 2, 3, 4, 6, 7]))))
        else:
            units = random.choice([str(random.randint(0, 50)), "x", "-2", "3.5", " 4 ", "", "007", "1,5"])
            price = random.choice([f"{random.randint(0, 99)}.{random.randint(0, 99):02d}", "5", "abc", "-1", " 2.50", "0", "1.005", "$3"])
            lines.append(",".join([f(), f(), f(), q(units), q(price)]))
    text = "\n".join(lines) + random.choice(["\n", "", "\n\n"])
    if random.random() < .15:
        text = text.replace("\n", "\r\n")
    if random.random() < .15:
        text = "﻿" + text
    return text


def run_hl(path, rest="", program="csv_report.hum"):
    p = subprocess.run([sys.executable, "-m", "humanlang", "run", os.path.join(HERE, program)], input=path + "\n",
                       capture_output=True, text=True, cwd=ROOT, env=ENV, timeout=300)
    return p.stdout.replace("CSV file: ", "", 1), p.stderr


def test4(n=60, program="csv_report.hum"):
    random.seed(4)
    exact = "exact" in program
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        for i in range(n):
            text = make_file()
            path = os.path.join(d, f"f{i}.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            # the program reads text files the way Python's open() does: line endings become \n, the BOM goes
            seen = text.replace("\r\n", "\n").lstrip("﻿")
            want, want_clean = model(seen, exact)
            got, err = run_hl(path, program=program)
            got = got.split("Wrote ")[0] if want_clean else got
            if want is None:
                continue
            ok = got == want
            if ok and want_clean:
                ok = open(path + ".clean", encoding="utf-8").read() == want_clean
            if not ok:
                bad += 1
                if bad <= 3:
                    print(f"--- file {i} differs\n{text!r}\nwant:\n{want}got:\n{got}{err}")
    print(f"test 4 ({program}): {n} random CSV files, {bad} disagreements with Python")
    return bad


def speed(rows=20000, program="csv_report.hum"):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "big.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("date,region,product,units,price\n")
            for i in range(rows):
                f.write(f"2026-01-01,{random.choice(['N','S','E','W'])},P{i % 50},{i % 9},{(i % 90) / 10:.2f}\n")
        size = os.path.getsize(path)
        t = time.time()
        got, err = run_hl(path, program=program)
        print(f"speed: {rows} rows ({size // 1000} KB) in {time.time() - t:.1f} s; first line: {got.splitlines()[0] if got else err[:80]}")


# ---------------- 5. the multi-module library project ----------------
def library_model(cmds):
    books, members, out, fees, errors = {}, {}, [], 0, 0
    for line in cmds:
        w = line.split(" ")
        try:
            c = w[0]
            if c == "book":
                if w[1] in books:
                    raise ValueError(f"book {w[1]} already exists")
                if int(w[2]) < 1:
                    raise ValueError("a book needs at least 1 copy")
                books[w[1]] = {"title": " ".join(w[3:]), "copies": int(w[2]), "out": 0}
                out.append(f"ok: added {' '.join(w[3:])}")
            elif c == "join":
                if w[1] in members:
                    raise ValueError(f"member {w[1]} already exists")
                members[w[1]] = []
                out.append(f"ok: welcome {w[1]}")
            elif c == "borrow":
                if not w[3].isdigit():
                    raise ValueError("day must be a whole number")
                n, b = w[1], w[2]
                if n not in members:
                    raise ValueError(f"no member {n}")
                if len(members[n]) >= 2:
                    raise ValueError(f"{n} already has 2 books")
                if any(i == b for i, d in members[n]):
                    raise ValueError(f"{n} already has {b}")
                if b not in books:
                    raise ValueError(f"no book {b}")
                if books[b]["out"] >= books[b]["copies"]:
                    raise ValueError(f"all copies of {b} are out")
                books[b]["out"] += 1
                members[n].append((b, int(w[3])))
                out.append(f"ok: {n} borrowed {b}")
            elif c == "return":
                if not w[3].isdigit():
                    raise ValueError("day must be a whole number")
                n, b = w[1], w[2]
                if n not in members:
                    raise ValueError(f"no member {n}")
                loan = next((x for x in members[n] if x[0] == b), None)
                if loan is None:
                    raise ValueError(f"{n} does not have {b}")
                members[n].remove(loan)
                books[b]["out"] -= 1
                fee = max(0, int(w[3]) - loan[1] - 14) * 10
                fees += fee
                out.append(f"ok: {n} returned {b}, fee {fee // 100}.{fee % 100:02d}")
            elif c == "books":
                out.append("ID    TITLE                  OUT  OF")
                for i in sorted(books, key=lambda x: (x.casefold(), x)):
                    k = books[i]
                    out.append(i.ljust(6) + k["title"].ljust(22) + str(k["out"]).rjust(4) + str(k["copies"]).rjust(4))
            elif c == "members":
                for n in sorted(members, key=lambda x: (x.casefold(), x)):
                    out.append(n.ljust(10) + ", ".join(i for i, d in members[n]))
            else:
                raise ValueError(f"unknown command {c}")
        except ValueError as e:
            errors += 1
            out.append(f"error: {e}")
    out.append(f"Fees collected: {fees // 100}.{fees % 100:02d}. Errors: {errors}.")
    return out


def random_session():
    names, ids = ["ann", "bob", "cy", "Dee"], [f"b{i}" for i in range(1, 6)]
    cmds = []
    for _ in range(random.randint(5, 60)):
        r = random.random()
        if r < .12:
            cmds.append(f"book {random.choice(ids)} {random.choice([0, 1, 1, 2, 3])} {random.choice(['Dune', 'A Long Title', '', 'Emma'])}".rstrip(" ") if random.random() < .9 else f"book {random.choice(ids)} 2")
        elif r < .22:
            cmds.append(f"join {random.choice(names + ['eve'])}")
        elif r < .5:
            cmds.append(f"borrow {random.choice(names)} {random.choice(ids + ['zz'])} {random.choice([str(random.randint(1, 40))] * 6 + ['x', '-3', '2.5'])}")
        elif r < .75:
            cmds.append(f"return {random.choice(names)} {random.choice(ids)} {random.choice([str(random.randint(1, 60))] * 6 + ['x'])}")
        elif r < .85:
            cmds.append("books")
        elif r < .92:
            cmds.append("members")
        else:
            cmds.append(random.choice(["fly", "BORROW", "x y z"]))
    return cmds


def test5(n=40):
    random.seed(5)
    subprocess.run([sys.executable, os.path.join(HERE, "project", "build.py")], check=True, capture_output=True)
    bad = 0
    for i in range(n):
        cmds = random_session()
        p = subprocess.run([sys.executable, "-m", "humanlang", "run", os.path.join(HERE, "project", "library.hum")],
                           input="\n".join(cmds + ["quit"]) + "\n", capture_output=True, text=True, cwd=ROOT, env=ENV)
        got = [l.strip() if l.startswith(" ") else l for l in p.stdout.replace("> ", "\n").splitlines() if l.strip() != ""]
        got = [l.rstrip() for l in got]
        want = [l.rstrip() for l in library_model(cmds)]
        if got != want:
            bad += 1
            if bad <= 2:
                print(f"--- session {i}\n" + "\n".join(cmds) + "\nwant/got first difference:")
                for a, c in zip(want, got):
                    if a != c:
                        print("  want", repr(a), "got", repr(c))
                        break
                print(" ", len(want), "vs", len(got), "lines", p.stderr[:200])
    print(f"test 5: {n} random sessions of the library project, {bad} disagreements with Python")
    return bad


if __name__ == "__main__":
    which = sys.argv[1:] or ["4"]
    if "4" in which:
        test4()
        test4(program="csv_report_exact.hum")
    if "5" in which:
        test5()
    if "speed" in which:
        speed()
