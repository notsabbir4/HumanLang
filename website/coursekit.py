"""The shared parts of the interactive courses (Beginner+, Designer Go, Game Maker, Master 2.0).

A course is a Python module with SKILLS, TAGS and UNITS (see website/beginner.py). This file holds what they all share:

  * how an exercise is written (P, T, F, O, B, W, K, C, PG, GV, part, unit)
  * how a program is RUN to check an answer (text programs, pages and games)
  * how a course is turned into the data the web page plays (export_json)
  * how every exercise is verified (problems): the tests run it, so a right answer is what HumanLang really does.
"""
import base64
import html as _html
import itertools
import json
import os
import re
import sys
import tempfile
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402
from humanlang.render import to_html  # noqa: E402

sys.setrecursionlimit(20000)


# =====================================================================================================
# Running programs
# =====================================================================================================
def _interp(inputs):
    out, answers = [], list(inputs)

    def inp(prompt):
        if not answers:
            raise EOFError
        a = answers.pop(0)
        out.append(prompt + a + "\n")
        return a

    return out, Interpreter(out=out.append, inp=inp)


def run(code, inputs=()):
    """(output_text, error_text_or_None) exactly as the terminal would show them."""
    out, interp = _interp(inputs)
    err = None
    try:
        _in_temp(lambda: interp.run(code))
    except HLError as e:
        err = e.format(code.splitlines())
    return "".join(out), err


def _in_temp(fn):
    old = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            return fn()
        finally:
            os.chdir(old)


def _globals(interp):
    """What the program's own variables hold, as text (numbers, text, yes/no only)."""
    parts = []
    for k in sorted(interp.globals.vars):
        v = interp.globals.vars[k]
        if isinstance(v, (bool, int, float, str)) or type(v).__name__ == "Decimal":
            parts.append(f"{k}={interp.show(v)}")
    return ", ".join(parts)


def page_of(code):
    """(html_document_or_None, error_or_None): the last page the program shows."""
    out, interp = _interp([])
    try:
        _in_temp(lambda: interp.run(code))
    except HLError as e:
        return None, e.format(code.splitlines())
    return (to_html(interp.designs[-1]) if interp.designs else None), None


def body_of(doc):
    return doc[doc.index("<body"):] if doc and "<body" in doc else (doc or "")


def page_fact(doc, how):
    """A fact about a page, as text. how: ("count", "button") | ("text", "h1") | ("texts", "button") | ("has", "...")."""
    b = body_of(doc)
    kind, what = how[0], how[1]
    if kind == "count":
        return str(len(re.findall(rf"<{what}\b", b)))
    if kind == "text":
        m = re.search(rf"<{what}\b[^>]*>(.*?)</{what}>", b, re.S)
        return _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))) if m else ""
    if kind == "texts":
        return ", ".join(_html.unescape(re.sub(r"<[^>]+>", "", t)) for t in re.findall(rf"<{what}\b[^>]*>(.*?)</{what}>", b, re.S))
    if kind == "has":
        return "yes" if what in b else "no"
    raise ValueError(how)


def game_value(code, var, frames, down=(), pressed=(), inputs=()):
    """Run a game for some frames (keys held the whole time; `pressed` once, on the first frame) and read a variable."""
    out, interp = _interp(inputs)

    def go():
        interp.run(code)
        if interp.game is None:
            raise HLError("Line 1: no game")
        for i in range(frames):
            interp.game_frame(down=list(down), pressed=list(pressed) if i == 0 else [])
        e = interp.globals.find(var)
        return interp.show(e.vars[var]) if e else None
    try:
        return _in_temp(go), None
    except HLError as e:
        return None, e.format(code.splitlines())


def rich_run(code, inputs=()):
    """Like run(), but also tells what a page or a game does, so two programs can be compared:
    the output text, then the page's body, then the game's variables after 20 frames (and 20 more with the right key held)."""
    out, interp = _interp(inputs)
    err = None

    def go():
        interp.run(code)
        extra = []
        if interp.designs:
            extra.append("[page] " + body_of(to_html(interp.designs[-1])))
        if interp.game is not None:
            for i in range(20):
                interp.game_frame()
            for i in range(20):
                interp.game_frame(down=["right"], pressed=["space"] if i == 0 else [])
            extra.append("[game] " + _globals(interp))
        return extra
    try:
        extra = _in_temp(go)
    except HLError as e:
        return "".join(out), e.format(code.splitlines())
    return "".join(out) + "".join(x + "\n" for x in extra), err


# =====================================================================================================
# How an exercise is written
# =====================================================================================================
def _opts(right, wrong):
    o = [{"t": right, "ok": True}]
    for w in wrong:
        t, tag = (w, "other") if isinstance(w, str) else w
        o.append({"t": t, "ok": False, "tag": tag})
    return o


def P(code, right, wrong, skill, why, inputs=(), error=False, q=None):
    """Predict: what does this program print? (error=True: what does HL say?)"""
    return {"kind": "predict", "code": code, "inputs": list(inputs), "error": error, "skill": skill, "why": why, "q": q,
            "options": _opts(right, wrong)}


def PG(code, q, how, right, wrong, skill, why):
    """Predict a fact about the PAGE this program shows (the page is shown next to the code).
    how = ("count", "button") | ("text", "h1") | ("texts", "button") | ("has", "<css or html text>")."""
    return {"kind": "predict", "code": code, "inputs": [], "error": False, "skill": skill, "why": why, "q": q, "fact": list(how),
            "show": True, "options": _opts(right, wrong)}


def T(code, skill, why, inputs=(), q=None):
    """Type what the program prints (the answer is worked out by really running it)."""
    return {"kind": "type", "code": code, "inputs": list(inputs), "skill": skill, "why": why, "q": q}


def F(code, accept, skill, why, wrong=(), inputs=(), q=None, show=False):
    """Fill the gap (___) so the program works. show=True: the program is a page; show it when the answer is right."""
    return {"kind": "fill", "code": code, "accept": list(accept), "inputs": list(inputs), "skill": skill, "why": why,
            "wrong": list(wrong), "q": q, "show": show}


def O(lines, skill, why, inputs=(), q=None, show=False):
    """Put the lines in order."""
    return {"kind": "order", "lines": list(lines), "inputs": list(inputs), "skill": skill, "why": why, "q": q, "show": show}


def B(code, bad, skill, why, fix, goal=None, inputs=(), q=None):
    """Tap the line that has the mistake. fix = the corrected line. goal = what it should print (when the bug is silent)."""
    return {"kind": "bug", "code": code, "bad": bad, "fix": fix, "goal": goal, "inputs": list(inputs), "skill": skill,
            "why": why, "q": q}


def W(task, accept, skill, why, wrong=(), ctx="", goal=None, inputs=(), indent=0, show=False):
    """Write one line of HumanLang. indent: the line sits inside the last line of ctx (4 spaces per level).
    show=True: ctx + the line make a page; show it when the answer is right."""
    return {"kind": "write", "task": task, "accept": list(accept), "ctx": ctx, "goal": goal, "inputs": list(inputs), "skill": skill,
            "why": why, "wrong": list(wrong), "indent": indent, "show": show}


def K(code, var, right, wrong, skill, why):
    """Trace: after the last line has run, what is in a variable? (this is what Step through shows you)"""
    return {"kind": "trace", "code": code, "var": var, "inputs": [], "skill": skill, "why": why, "options": _opts(right, wrong)}


def GV(code, var, frames, right, wrong, skill, why, down=(), pressed=(), q=None):
    """Follow a GAME: the keys are held for some frames. What is inside a variable afterwards?"""
    keys = ""
    if down:
        keys = "Hold the " + " and ".join(down) + " key" + ("s" if len(down) > 1 else "") + " for "
    elif pressed:
        keys = "Press " + " and ".join(pressed) + " once, then wait for "
    else:
        keys = "Touch no keys and wait for "
    return {"kind": "trace", "code": code, "var": var, "inputs": [], "skill": skill, "why": why, "options": _opts(right, wrong),
            "game": {"frames": frames, "down": list(down), "pressed": list(pressed)},
            "q": q or f"{keys}{frames} frame{'s' if frames != 1 else ''}. What is inside {var} then?"}


def C(q, right, wrong, skill, why, code=None, show=False):
    """A plain multiple-choice question (with an optional program to look at)."""
    return {"kind": "choose", "q": q, "code": code, "inputs": [], "skill": skill, "why": why, "options": _opts(right, wrong), "show": show}


def part(title, teach, *ex):
    return {"title": title, "teach": teach.strip("\n") + "\n", "ex": list(ex)}


def unit(n, title, blurb, parts, bank):
    return {"n": n, "title": title, "blurb": blurb, "parts": parts, "bank": bank}


def lines_of(*pieces):
    """Join pieces of code with newlines (for readability in the course files)."""
    return "\n".join(pieces)


# =====================================================================================================
# What the web page gets (every answer was worked out here, by running it: the page has no HumanLang inside)
# =====================================================================================================
_BLOCK = re.compile(r"```(hum|hum-error)\n(.*?)```(\s*```input\n(.*?)```)?", re.S)


def expand(md, runner):
    """Teach text: after every example, add what HL really prints (or says)."""
    def sub(m):
        kind, body, given = m.group(1), m.group(2), m.group(4)
        out, err = runner(body, inputs=given.split("\n")[:-1] if given else ["Sam", "20", "20", "20"])
        text = (err if kind == "hum-error" else out).rstrip("\n")
        res = f"```{kind}\n{body}```\n"
        if given:
            res += f"\n```input\n{given}```\n"
        if text:
            res += f"\n```output\n{text}\n```\n"
        return res
    text = _BLOCK.sub(sub, md)
    # a game needs the Playground to run: put a link under every game example
    return re.sub(r"```hum-game\n(.*?)```\n", lambda m: m.group(0) + f"\n[Run this game in the Playground]({playground_link(m.group(1))})\n", text, flags=re.S)


def playground_link(code):
    q = urllib.parse.quote(base64.b64encode(code.encode("utf-8")).decode("ascii"), safe="")
    return f"playground.html#code={q}"


def _srcdoc(doc):
    return doc if doc else None


def full_program(e, answer=None):
    """The whole program of an exercise with an answer put in (fill and write)."""
    if e["kind"] == "fill":
        return e["code"].replace("___", answer if answer is not None else e["accept"][0])
    if e["kind"] == "write":
        a = answer if answer is not None else e["accept"][0]
        return (e["ctx"] + "\n" if e["ctx"] else "") + " " * (4 * e.get("indent", 0)) + a
    if e["kind"] == "order":
        return "\n".join(e["lines"])
    return e.get("code") or ""


def _ex(e, eid, highlight, runner):
    d = dict(e)
    d["id"] = eid
    if e.get("code"):
        d["html"] = highlight(e["code"])
    if e["kind"] == "type":
        d["answer"] = runner(e["code"], e["inputs"])[0].rstrip("\n")
    if e["kind"] == "write" and e.get("ctx"):
        d["ctx_html"] = highlight(e["ctx"])
    if e["kind"] == "bug":
        d["lines"] = e["code"].split("\n")
    if e["kind"] == "order":
        d["goal_out"] = runner("\n".join(e["lines"]), e["inputs"])[0].rstrip("\n")
    d["wrong"] = [[w[0], w[1]] for w in e.get("wrong", [])]
    if e.get("show"):
        # a picture of the page: shown beside the question (predict, choose) or as a reward when the answer is right
        prog = full_program(e) if e["kind"] in ("fill", "write", "order") else e.get("code")
        doc, err = page_of(prog) if prog else (None, None)
        if doc:
            d["page"] = doc
    d.pop("show", None)
    return d


def export(mod, render_markdown, highlight):
    runner = getattr(mod, "run", run)
    units = []
    for u in mod.UNITS:
        n = u["n"]
        parts = []
        for pi, p in enumerate(u["parts"], 1):
            html_, _ = render_markdown(expand(p["teach"], runner))
            parts.append({"title": p["title"], "teach": html_,
                          "ex": [_ex(e, f"u{n}p{pi}e{i}", highlight, runner) for i, e in enumerate(p["ex"], 1)]})
        units.append({"n": n, "title": u["title"], "blurb": u["blurb"], "parts": parts,
                      "bank": [_ex(e, f"u{n}b{i}", highlight, runner) for i, e in enumerate(u["bank"], 1)]})
    c = dict(mod.COURSE)
    return {"course": c, "units": units, "skills": mod.SKILLS, "tags": {k: v[1] for k, v in mod.TAGS.items()},
            "tagSkill": {k: v[0] for k, v in mod.TAGS.items()}}


def export_json(mod, render_markdown, highlight):
    return json.dumps(export(mod, render_markdown, highlight), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# =====================================================================================================
# Checking every exercise (used by the tests): returns a list of problems, [] = fine
# =====================================================================================================
def first_line(err):
    return err.split("\n")[0]


def exercises(u):
    for pi, p in enumerate(u["parts"], 1):
        for ei, e in enumerate(p["ex"], 1):
            yield f"unit {u['n']} part {pi} exercise {ei}", e
    for ei, e in enumerate(u["bank"], 1):
        yield f"unit {u['n']} bank {ei}", e


def problems(e, mod):
    rr = getattr(mod, "run", run)
    bad = []
    k, inputs = e["kind"], e["inputs"]
    if e["skill"] not in mod.SKILLS:
        bad.append(f"unknown skill {e['skill']}")
    if not e["why"].strip():
        bad.append("no explanation")
    for o in e.get("options", []):
        if not o["ok"] and o["tag"] not in mod.TAGS:
            bad.append(f"unknown tag {o['tag']}")
    for w in e.get("wrong", []):
        if w[1] not in mod.TAGS:
            bad.append(f"unknown tag {w[1]}")
    if e.get("options"):
        texts = [o["t"] for o in e["options"]]
        if len(set(texts)) != len(texts):
            bad.append("two options are the same")
        if sum(1 for o in e["options"] if o["ok"]) != 1:
            bad.append("needs exactly one right option")
    if k == "predict" and e.get("fact"):
        doc, err = page_of(e["code"])
        want = [o["t"] for o in e["options"] if o["ok"]][0]
        if err or doc is None:
            bad.append(f"the page does not build: {err!r}")
        elif page_fact(doc, e["fact"]) != want:
            bad.append(f"the page says {page_fact(doc, e['fact'])!r}, not {want!r}")
    elif k == "predict":
        out, err = rr(e["code"], inputs)
        want = [o["t"] for o in e["options"] if o["ok"]][0]
        if e["error"]:
            if err is None or first_line(err) != want:
                bad.append(f"error text is {err!r}")
        elif err or out.rstrip("\n") != want:
            bad.append(f"prints {out!r} (error {err!r}), not {want!r}")
    elif k == "type":
        out, err = rr(e["code"], inputs)
        if err or not out.strip():
            bad.append(f"does not print anything useful: {err!r}")
    elif k == "fill":
        outs = set()
        for a in e["accept"]:
            out, err = rr(full_program(e, a), inputs)
            if err:
                bad.append(f"fill {a!r} fails: {err}")
            outs.add(out)
            if e.get("show") and not page_of(full_program(e, a))[0]:
                bad.append(f"fill {a!r} does not make a page")
        if len(outs) > 1:
            bad.append("the accepted answers do different things")
        for pat, tag in e["wrong"]:
            for a in e["accept"]:
                if re.search(pat, a):
                    bad.append(f"wrong pattern {pat} matches the right answer {a!r}")
    elif k == "order":
        good = "\n".join(e["lines"])
        want, err = rr(good, inputs)
        if err:
            bad.append(f"the right order fails: {err}")
        if e.get("show") and not page_of(good)[0]:
            bad.append("the lines do not make a page")
        if len(e["lines"]) > 6:
            bad.append("too many lines for a unique-order check")
        else:
            seen = set()
            for perm in itertools.permutations(e["lines"]):
                if perm in seen or list(perm) == e["lines"]:
                    continue
                seen.add(perm)
                out, perr = rr("\n".join(perm), inputs)
                if not perr and out == want:
                    bad.append(f"another order also works: {perm}")
                    break
    elif k == "bug":
        lines = e["code"].split("\n")
        out, err = rr(e["code"], e["inputs"])
        if not 1 <= e["bad"] <= len(lines):
            return bad + [f"the bad line {e['bad']} is not in the program ({len(lines)} lines)"]
        fixed = lines[:]
        fixed[e["bad"] - 1] = e["fix"]
        fout, ferr = rr("\n".join(fixed), e["inputs"])
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
            prog = full_program(e, a)
            out, err = rr(prog, inputs=e["inputs"] or ["x", "5", "5", "5"])
            if err and "indented block" in err:                  # the line opens a block: give it a body
                out, err = rr(prog + '\n' + " " * (4 * e.get("indent", 0) + 4) + 'say "x"', inputs=e["inputs"] or ["x", "5", "5", "5"])
            if err:
                bad.append(f"accepted line {a!r} fails: {err}")
            elif e["goal"] is not None and out.rstrip("\n") != e["goal"]:
                bad.append(f"accepted line {a!r} prints {out!r}, not {e['goal']!r}")
            if e.get("show") and not page_of(prog)[0]:
                bad.append(f"accepted line {a!r} does not make a page")
            for pat, tag, *_ in [(w[0], w[1]) for w in e["wrong"]]:
                if re.search(pat, a):
                    bad.append(f"wrong pattern {pat} matches the right answer")
    elif k == "choose":
        pass
    elif k == "trace":
        right = [o["t"] for o in e["options"] if o["ok"]]
        if e.get("game"):
            g = e["game"]
            val, err = game_value(e["code"], e["var"], g["frames"], g["down"], g["pressed"])
            if err:
                bad.append(f"the game fails: {err}")
            elif right != [val]:
                bad.append(f"trace right answer {right} but the game gives {val!r}")
        else:
            out, err = rr(e["code"] + "\nsay " + e["var"])
            if err:
                bad.append(f"trace program fails: {err}")
            elif right != [out.strip()]:
                bad.append(f"trace right answer {right} but program gives {out!r}")
    else:
        bad.append("unknown kind")
    return bad
