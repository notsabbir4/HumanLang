"""Beginner+ is an interactive course. Every exercise is checked by REALLY RUNNING it in HumanLang, so a right answer is
what HL prints, a fill-in-the-blank works, a puzzle has exactly one right order, and the bug is on the line we say."""
import itertools
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "website"))
import beginner as bp  # noqa: E402


def exercises(u):
    for pi, p in enumerate(u["parts"], 1):
        for ei, e in enumerate(p["ex"], 1):
            yield f"unit {u['n']} part {pi} exercise {ei}", e
    for ei, e in enumerate(u["bank"], 1):
        yield f"unit {u['n']} bank {ei}", e


def first_line(err):
    return err.split("\n")[0]


def check(e):
    """Returns a list of problems with this exercise ([] = fine)."""
    bad = []
    k, inputs = e["kind"], e["inputs"]
    if e["skill"] not in bp.SKILLS:
        bad.append(f"unknown skill {e['skill']}")
    if not e["why"].strip():
        bad.append("no explanation")
    for o in e.get("options", []):
        if not o["ok"] and o["tag"] not in bp.TAGS:
            bad.append(f"unknown tag {o['tag']}")
    for w in e.get("wrong", []):
        if w[1] not in bp.TAGS:
            bad.append(f"unknown tag {w[1]}")
    if k == "predict":
        out, err = bp.run(e["code"], inputs)
        want = [o["t"] for o in e["options"] if o["ok"]][0]
        if e["error"]:
            if err is None or first_line(err) != want:
                bad.append(f"error text is {err!r}")
        elif err or out.rstrip("\n") != want:
            bad.append(f"prints {out!r} (error {err!r}), not {want!r}")
        texts = [o["t"] for o in e["options"]]
        if len(set(texts)) != len(texts):
            bad.append("two options are the same")
    elif k == "type":
        out, err = bp.run(e["code"], inputs)
        if err or not out.strip():
            bad.append(f"does not print anything useful: {err!r}")
    elif k == "fill":
        outs = set()
        for a in e["accept"]:
            out, err = bp.run(e["code"].replace("___", a), inputs)
            if err:
                bad.append(f"fill {a!r} fails: {err}")
            outs.add(out)
        if len(outs) > 1:
            bad.append("the accepted answers print different things")
        for pat, tag in e["wrong"]:
            for a in e["accept"]:
                if re.search(pat, a):
                    bad.append(f"wrong pattern {pat} matches the right answer {a!r}")
    elif k == "order":
        good = "\n".join(e["lines"])
        want, err = bp.run(good, inputs)
        if err:
            bad.append(f"the right order fails: {err}")
        if len(e["lines"]) > 6:
            bad.append("too many lines for a unique-order check")
        else:
            seen = set()
            for perm in itertools.permutations(e["lines"]):
                if perm in seen or list(perm) == e["lines"]:
                    continue
                seen.add(perm)
                out, perr = bp.run("\n".join(perm), inputs)
                if not perr and out == want:
                    bad.append(f"another order also works: {perm}")
                    break
    elif k == "bug":
        lines = e["code"].split("\n")
        out, err = bp.run(e["code"], e["inputs"])
        fixed = lines[:]
        fixed[e["bad"] - 1] = e["fix"]
        fout, ferr = bp.run("\n".join(fixed), e["inputs"])
        if ferr:
            bad.append(f"the fixed program still fails: {ferr}")
        if e["goal"] is None:
            if err is None:
                bad.append("the program has no error, so give a goal")
            else:
                m = re.match(r"Line (\d+):", err)
                where = int(m.group(1)) + (1 if m and "indented block" in err else 0)   # a missing indent is reported on the line above
                if not m or where != e["bad"]:
                    bad.append(f"HL points at {err.splitlines()[0]!r}, not line {e['bad']}")
        else:
            if out == e["goal"] or fout.rstrip("\n") != e["goal"].rstrip("\n"):
                bad.append(f"goal check failed: before {out!r}, after {fout!r}")
    elif k == "write":
        for a in e["accept"]:
            prog = (e["ctx"] + "\n" if e["ctx"] else "") + a
            out, err = bp.run(prog, inputs=e["inputs"] or ["x", "5", "5", "5"])
            if err and "indented block" in err:                  # the line opens a block: give it a body
                out, err = bp.run(prog + '\n    say "x"', inputs=e["inputs"] or ["x", "5", "5", "5"])
            if err:
                bad.append(f"accepted line {a!r} fails: {err}")
            elif e["goal"] is not None and out.rstrip("\n") != e["goal"]:
                bad.append(f"accepted line {a!r} prints {out!r}, not {e['goal']!r}")
            for pat, tag, *_ in [(w[0], w[1]) for w in e["wrong"]]:
                if re.search(pat, a):
                    bad.append(f"wrong pattern {pat} matches the right answer")
    elif k == "choose":
        if sum(1 for o in e["options"] if o["ok"]) != 1:
            bad.append("needs exactly one right option")
        if e["code"]:
            _, err = bp.run(e["code"], inputs)
            # a program shown in a question may fail on purpose or loop forever; we only parse-check nothing here
    elif k == "trace":
        out, err = bp.run(e["code"] + "\nsay " + e["var"])
        right = [o["t"] for o in e["options"] if o["ok"]]
        if err:
            bad.append(f"trace program fails: {err}")
        elif right != [out.strip()]:
            bad.append(f"trace right answer {right} but program gives {out!r}")
        if len(right) != 1:
            bad.append("needs exactly one right option")
    else:
        bad.append("unknown kind")
    return bad


class BeginnerExercises(unittest.TestCase):
    def test_every_exercise_is_correct(self):
        count = 0
        for u in bp.UNITS:
            for where, e in exercises(u):
                count += 1
                with self.subTest(where=where, kind=e["kind"], code=e.get("code") or e.get("task")):
                    self.assertEqual(check(e), [])
        self.assertGreater(count, 100)

    def test_teach_examples_run(self):
        for u in bp.UNITS:
            for p in u["parts"]:
                with self.subTest(unit=u["n"], part=p["title"]):
                    for kind, body, given in re.findall(r"```(hum|hum-error)\n(.*?)```(?:\s*```input\n(.*?)```)?", p["teach"], re.S):
                        out, err = bp.run(body, inputs=given.split("\n")[:-1] if given else ["Sam", "20", "20", "20"])
                        if kind == "hum":
                            self.assertIsNone(err, body)
                        else:
                            self.assertIsNotNone(err, body)


if __name__ == "__main__":
    unittest.main()
